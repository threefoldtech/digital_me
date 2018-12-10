const client = (function(){
    let socket = new WebSocket(SERVER);
    let connected = false
    let connect = ()=> {
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
    let execute = (namespace, actor, command, args, headers) => {
        return connect().then((res) => {
            return new Promise((resolve, fail) => {
                let message = {
                    "command": `${namespace}.${actor}.${command}`,
                    "args": args,
                    "headers": headers,
                }
                socket.send(JSON.stringify(message))
                socket.onmessage = function(e) {
                    resolve(e.data)
                }
            })
        })
    }

    let client = {};
    client.execute = async (info) => {
        return await execute(info['namespace'], info['actor'], info['command'],
                             info['args'], info['headers'])
    };
    return client
})()

export {
    client as default
}
