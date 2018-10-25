#What is Digital ME publishing framework

It is an easy way that allows non technicals to create their own website using Markdowns.  

##How to create a website using Digital Me publishing Framework
I. Write your Markdown files (see this on how to create a markdown) [Markdown](https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet)

II.You need to write blueprint routes in order to make some functions for your website.

 * Load some dependencies.

    ```python
    import flask 
    from blueprints import *
    from Jumpscale import j
    ```
 * Load login manager.

    ```python
    login_manager = j.servers.web.latest.loader.login_manager
    ```
    
 * Load your docsites :
 
      Docsites is a framework used to load the md files created. 

    ```python
    j.tools.docsites.load(
        "https://The link to your md files",name="The name of your website")
    ```

 * Use the loaded docsites :
 
      To be able to use the content of the md files.
        
    ```python
    ds = j.tools.docsites.docsite_get("The name of your website")
    ```
 * Write your own blueprint routes for the md files

III. Call your routes in the html using jinja : 

* Use this notation ```{{The function name}} ``` to call the routes in the html using jinja.
    
* To get a link or image from md file use this where (nr) refers to the item number in the md file relative to each category, therefore nr=0 refers to the first link/image in the md file, and (cat) indicates the type of link to be returned (image, image link, doc, link)  
 
    ```html
    {{ doc.link_get(nr=0, cat= "image/doc/link/imagelink").link_source | safe }}
    ```    
* To get the description of the link call 

    ```html
    {{doc.link_get(nr=0).link_descr}}
    ```    
* To get the paragraph from the md file use this where (cat) is the category name (it could be: table, header, macro, code, comment1line, comment, block or data), and (nr) refers to the item number in the md file relative to each category. 

    ```html
    {{ doc.part_get(cat="block", nr=2).text | safe }}
    ```

