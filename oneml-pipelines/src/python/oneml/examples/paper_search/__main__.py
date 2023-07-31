from oneml.app import OnemlApp
from oneml.examples.paper_search._search_command import SearchServices

app = OnemlApp.default()
app.run_pipeline(SearchServices.MAIN)
