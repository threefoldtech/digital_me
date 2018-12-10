# What is Digital ME publishing framework

It is an easy way that allows non technicals to create their own website using Markdowns.  

## How to create a website using Digital Me publishing Framework

### Terminologies

Docsites:  is the md files you have to create

Templates: is the jinja templates you write inside html

BluePrint: Flask routes


### The structure of the project

- Create a a new project and create a new file called routes.py

- Write your routes inside that file and load the md file using the load code above.

- Create a folder called templates and create your html files inside it

- Write jinja code for your routes inside the html files

    

-   ├── routes.py

    └── Templates
        └──html files

### Write Markdown file
Write your Markdown files (see this on how to create a markdown) [Markdown](https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet)

### Blueprint Route
You need to write `blueprint` routes in order to make some functions for your website.

- Load some dependencies.

```python
import flask 
from blueprints.(The name of the folder directory inside blueprints) import *
from Jumpscale import j
```
- Load login manager.

```python
login_manager = j.servers.web.latest.loader.login_manager
```

- Load your docsites : Docsites is a framework used to load the md files created. 

```python
j.tools.docsites.load(
    "https://The link to your md files",name="The name of your website")
```

- Use the loaded docsites:
To be able to use the content of the md files
```python
    ds = j.tools.docsites.docsite_get("The name of your website")
```

- Write your own blueprint routes for the md files

### Use routes in templates

Call your routes in the html using jinja : 

- Use this notation ```{{The function name}} ``` to call the routes in the html using jinja.
    
- To get a link or image from md file use this route signature where (nr) refers to the item number in the md file relative to each category, therefore nr=0 refers to the first link/image in the md file, and (cat) indicates the type of link to be returned (image, image link, doc, link)  
 
    ```html
    {{ doc.link_get(nr=0, cat= "image/doc/link/imagelink").link_source | safe }}
    ```    
- To get the description of the link call 

    ```html
    {{doc.link_get(nr=0).link_descr}}
    ```    
- To get the paragraph from the md file use this where (cat) is the category name (it could be: table, header, macro, code, comment1line, comment, block or data), and (nr) refers to the item number in the md file relative to each category. 

    ```html
    {{ doc.part_get(cat="block", nr=2).text | safe }}
    ```

### Example Website

- inside the route file 
```python
from flask import render_template, redirect, send_file
from blueprints.hello import *
from Jumpscale import j
login_manager = j.servers.web.latest.loader.login_manager

j.tools.docsites.load(
    "https://github.com/threefoldtech/jumpscale_weblibs/tree/master/docsites_examples/simpleblogsite",
    name="man_explore")

ds = j.tools.docsites.docsite_get("man_explore")

@blueprint.route('/')
@blueprint.route('/hello')
def route_default():
    doc = ds.doc_get("man_explore")
    return render_template('hello.html', ds=ds, doc=doc)

``` 

- Load the data of the website from the (man_explore) docsite(md file).

- Crete __init.py__ file and write this code inside it
```python

from flask import Blueprint
from Jumpscale import j

name =  j.sal.fs.getDirName(__file__,True)
print("NAME::: ", name)
blueprint = Blueprint(
    '%s_blueprint'%name,
    __name__,
    url_prefix="/%s"%name,
    template_folder='templates',
    static_folder='static'
)

```

- Create your html file inside templates folder in the project and write this

```html
<!DOCTYPE html>
<html lang="en">  

<body>
<h2 class="mt-0">{{ doc.part_get(cat="header", nr=0).title}}</h2>
</body>

</html>
 ```
 
- Run your code using this command (js_shell 'j.servers.digitalme.start()').