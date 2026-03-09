import os, sys, pyang
from pyang import context, repository, plugin

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(''), "..", "data"))
yang_dir = os.path.join(DATA_DIR, "bbf_yang", "standard")
repos = pyang.repository.FileRepository(yang_dir)
ctx = pyang.context.Context(repos)
pyang.plugin.init([])
# Must initialize context with options
optparser = pyang.options.get_options_parser()
for p in pyang.plugin.plugins:
    p.add_opts(optparser)
opts, args = optparser.parse_args([])
ctx.opts = opts
ctx.opts.depend_from_submodules = False

model_path = os.path.join(yang_dir, "common", "bbf-device.yang")
with open(model_path, 'r', encoding='utf-8') as fd:
    text = fd.read()

module = ctx.add_module(model_path, text)
print(f"Module added: {module.arg if module else 'Failed'}")
if module:
    ctx.validate()
    print("Pre-validation done")
    # Actually need to call validate() on the context over the module, or check module.i_children after
    for child in getattr(module, 'i_children', []):
        print(f" - child: {child.arg}")
    
    # Try traversing substmts
    print("Checking substmts:")
    for child in getattr(module, 'substmts', []):
        print(f" - substmt: {child.keyword} {child.arg}")
