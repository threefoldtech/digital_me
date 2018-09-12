// SERVER_DOMAIN & SERVER_PORT will come from the client.js 
const client = (function(){
    var socket = new WebSocket("%%host%%");
    var connected = false
    var connect = ()=> {
        return new Promise(res =>{
            if(!connected){
                socket.onopen = () => {
                connected = true
                res(true)
            }
            } else {
                res(true)
            }
        })
      }
      var execute = (command, args) => {
          return connect().then((res) => { return new Promise((resolve, fail) => {
              socket.onmessage = function(e) {
                  resolve(e.data)
              }
              if (args.length != 0){
                  var message = {
                    "command": command,
                    "args": args
                  }
                  socket.send(JSON.stringify(message))
              } else {
                  socket.send(command)
              }
          })})
      }
    
    var client = {}
    
    {% for command in commands %}
    client.{{command.data.namespace.split('.')[1]}} = {
    {% for  name, cmd in command.cmds.items() %}
        "{{name}}": async ({{cmd.args_client.strip(",").replace("False", "false").replace("True", "true") if cmd.args_client.strip() != ",schema_out" else ""}}) => {
        {% if cmd.schema_in %}
            var args = {}
            {% for prop in cmd.schema_in.properties + cmd.schema_in.lists %}
            {% if prop.jumpscaletype.NAME != 'list' %}
            args["{{prop.name}}"] = {{prop.name}}
            {% else %}
            args["{{prop.name}}"] = []
            {{prop.name}}.forEach(function(item){args["{{prop.name}}"].push(item)})
            {% endif %}
            {% endfor %}
            return await execute("{{command.data.namespace.split('.')[1]}}.{{name}}", JSON.stringify(args))
        {% else %}
            return await execute("{{command.data.namespace.split('.')[1]}}.{{name}}", "")
        {% endif %}
        },
    {% endfor %}
    }
    {% endfor %}
return client    
})()
export {
    client as default
} 