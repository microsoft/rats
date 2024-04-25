Source files for docs/notebooks/.

To update, run the following here, and then copy *.md files and *_files folders to docs/notebooks/.

```bash
jupytext --to ipynb *.py
jupyter nbconvert *.ipynb --to markdown --execute --TemplateExporter.extra_template_basedirs=../../resources/nbconvert_templates --template=mdoutput
```
