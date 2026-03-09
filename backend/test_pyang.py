import os, sys, pyang
from pyang import context, repository

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(''), "..", "data"))
def _find_yang_file(filename: str) -> str:
    yang_dir = os.path.join(DATA_DIR, "bbf_yang", "standard")
    for root_dir, dirs, files in os.walk(yang_dir):
        if filename in files:
            return os.path.join(root_dir, filename)
    return None

yang_dir = os.path.join(DATA_DIR, "bbf_yang", "standard")
repos = pyang.repository.FileRepository(yang_dir)
ctx = pyang.context.Context(repos)
ctx.opts = pyang.options.get_options_parser().parse_args([])[0]
ctx.opts.depend_from_submodules = False

model_name = "bbf-device.yang"
file_path = _find_yang_file(model_name)
if not file_path:
    print(f"Cannot find file in {yang_dir}")
    sys.exit(1)

with open(file_path, 'r', encoding='utf-8') as fd:
    text = fd.read()

module = ctx.add_module(file_path, text)
print(f"Module added: {module.arg}")
ctx.validate()
print(f"Module validated, attributes:")

if hasattr(module, "i_children"):
    print(f"Children (i_children): {len(module.i_children)}")
    for child in module.i_children:
        print(f" - {child.keyword} {child.arg}")
else:
    print("No i_children attribute.")

if hasattr(module, "substmts"):
    print(f"Children (substmts): {len(module.substmts)}")
    for child in module.substmts:
        print(f" - {child.keyword} {child.arg}")
