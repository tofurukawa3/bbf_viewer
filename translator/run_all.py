import subprocess
import time
import sys
import re

files_to_translate = [
    "tr-181-2-20-1-cwmp-full.xml",
    "tr-196-2-1-2-cwmp-full.xml",
    "tr-262-1-0-0.xml"
]

def run_loop():
    for f in files_to_translate:
        print(f"\n{'='*50}\nStarting auto-translation loop for {f}...\n{'='*50}")
        retry_count = 0
        MAX_RETRIES = 10
        while retry_count < MAX_RETRIES:
            process = subprocess.Popen(
                [sys.executable, "translate_models.py", "--file", f],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            output = ""
            for line in iter(process.stdout.readline, ''):
                sys.stdout.write(line)
                sys.stdout.flush()
                output += line
            
            process.wait()
            
            # Check for success metric
            m = re.search(r"Errors:\s*(\d+)", output[-1000:]) if len(output) > 1000 else re.search(r"Errors:\s*(\d+)", output)
            err_count = -1
            if m:
                err_count = int(m.group(1))

            if err_count == 0 and process.returncode == 0:
                print(f"\n[SUCCESS] File {f} translated successfully with 0 errors!")
                break
            else:
                retry_count += 1
                rc = process.returncode
                print(f"\n[RETRY {retry_count}/{MAX_RETRIES}] Process ended with Errors: {err_count} or return code {rc}. Retrying in 5 seconds...")
                time.sleep(5)
        
        if retry_count >= MAX_RETRIES:
            print(f"\n[GAVE UP] Exceeded {MAX_RETRIES} retries for {f}. Moving to next file.")

if __name__ == "__main__":
    run_loop()
