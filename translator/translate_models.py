import os
import re
import json
import logging
import argparse
from lxml import etree
from deep_translator import GoogleTranslator
from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "cwmp-data-models")
CACHE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "translation_cache.json"
)

# The maximum character length a single request is allowed to have (we use 4500 to leave padding for delimiters)
MAX_BATCH_LENGTH = 4500
DELIMITER = " ||| "


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def clean_text(text):
    if not text:
        return ""
    # Replace all whitespace sequences (including newlines and tabs) with a single space, 
    # then strip leading/trailing spaces to form a continuous plain text sentence.
    return re.sub(r"\s+", " ", text).strip()


def translate_batch(translator, batch_texts, cache):
    if not batch_texts:
        return [], 0

    # Join the texts with the delimiter
    combined_text = DELIMITER.join(batch_texts)

    try:
        translated_combined = translator.translate(combined_text)
        # Split back to list
        translated_list = [t.strip() for t in translated_combined.split("|||")]

        # If the API messed up the delimiter count, fallback to individual translation
        err_count = 0
        if len(translated_list) != len(batch_texts):
            logging.warning(
                f"Batch dimension mismatch: Expected {len(batch_texts)}, got {len(translated_list)}. Falling back to individual translation."
            )
            translated_list = []
            for text in batch_texts:
                try:
                    t = translator.translate(text)
                    translated_list.append(t)
                    cache[text] = t
                except Exception as e:
                    logging.error(f"Individual translation failed: {str(e)[:100]}")
                    translated_list.append(text)
                    err_count += 1
            return translated_list, err_count

        # Update Cache
        for orig, trans in zip(batch_texts, translated_list):
            cache[orig] = trans

        return translated_list, 0
    except Exception as e:
        logging.error(f"Batch translation failed: {str(e)[:100]}")
        return batch_texts, len(
            batch_texts
        )  # Return original texts on error so we don't wipe data


def translate_cwmp_model(filename="tr-181-2-16-0-cwmp-full.xml"):
    source_path = os.path.join(DATA_DIR, filename)
    name, ext = os.path.splitext(filename)
    dest_path = os.path.join(DATA_DIR, f"{name}-ja{ext}")

    if not os.path.exists(source_path):
        logging.error(f"Source model {source_path} does not exist.")
        return

    logging.info(f"Loading CWMP model: {source_path}")

    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(source_path, parser)
    root = tree.getroot()

    description_nodes = root.xpath("//*[local-name()='description']")
    total_nodes = len(description_nodes)
    logging.info(f"Found {total_nodes} <description> tags to process.")

    translator = GoogleTranslator(source="en", target="ja")
    cache = load_cache()

    # Pre-filter to finding nodes that ACTUALLY need translation (not empty, not cached)
    nodes_to_translate = []
    cached_count = 0

    for node in description_nodes:
        original_text = node.text
        if not original_text or not original_text.strip():
            continue

        clean_original = clean_text(original_text)

        if clean_original in cache:
            node.text = cache[clean_original]
            cached_count += 1
        else:
            nodes_to_translate.append((node, clean_original))

    logging.info(f"Using {cached_count} translations from cache.")
    logging.info(
        f"Starting API batch translation for {len(nodes_to_translate)} remaining tags."
    )

    error_count = 0
    translated_count = 0

    current_batch_nodes = []
    current_batch_texts = []
    current_batch_len = 0

    try:
        # Wrap the execution list in tqdm for visual progress
        with tqdm(
            total=len(nodes_to_translate), desc="Processing Batches", unit="tags"
        ) as pbar:
            for node, clean_text_str in nodes_to_translate:
                # If a single node is massive, skip or chop it so it doesn't break batching
                if len(clean_text_str) > MAX_BATCH_LENGTH:
                    logging.warning(f"Tag exceeds {MAX_BATCH_LENGTH} chars, skipping.")
                    pbar.update(1)
                    error_count += 1
                    continue

                # Check if adding this text pushes us over the batch limit
                estimated_addition = len(clean_text_str) + len(DELIMITER)

                if current_batch_len + estimated_addition > MAX_BATCH_LENGTH:
                    # Send the current batch to the API
                    translated_texts, err = translate_batch(
                        translator, current_batch_texts, cache
                    )
                    error_count += err
                    if err == 0:
                        translated_count += len(current_batch_texts)

                    # Map the translations back to the XML nodes
                    for n, t in zip(current_batch_nodes, translated_texts):
                        n.text = t

                    # Save cache periodically
                    save_cache(cache)

                    pbar.update(len(current_batch_nodes))

                    # Reset the batch
                    current_batch_nodes = []
                    current_batch_texts = []
                    current_batch_len = 0

                # Add current item to batch
                current_batch_nodes.append(node)
                current_batch_texts.append(clean_text_str)
                current_batch_len += estimated_addition

            # Process the final leftover batch
            if current_batch_nodes:
                translated_texts, err = translate_batch(
                    translator, current_batch_texts, cache
                )
                error_count += err
                if err == 0:
                    translated_count += len(current_batch_texts)
                for n, t in zip(current_batch_nodes, translated_texts):
                    n.text = t
                pbar.update(len(current_batch_nodes))
                save_cache(cache)

    except KeyboardInterrupt:
        logging.warning(
            "Translation process interrupted by user. Saving cache and exiting."
        )
    finally:
        save_cache(cache)
        logging.info(
            f"Translation finished. Fresh API hits: {translated_count}, Cache hits: {cached_count}, Errors: {error_count}"
        )

    logging.info(f"Saving translated model to {dest_path}")
    tree.write(dest_path, xml_declaration=True, encoding="UTF-8", pretty_print=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Translate TR-069 CWMP Model descriptions to Japanese (Batched PoC)"
    )
    parser.add_argument(
        "--file",
        type=str,
        default="tr-181-2-16-0-cwmp-full.xml",
        help="Target filename in data/cwmp-data-models/",
    )
    args = parser.parse_args()

    translate_cwmp_model(args.file)
