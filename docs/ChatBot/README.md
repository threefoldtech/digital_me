# Chatbot
 
The chatbot is a component of gedis server. It enables you to interact with user in a direct way using easily created chatflows. The actual code resides [here](../../DigitalMeLib/servers/gedis/GedisChatBot.py).
Though to be able to start a new sessions you can't communicate with the library directly, you will need to communicate with the it using the [chat actor](../../packages/system/chat/actors/chatbot.py) from the chat package.


# Chat Actor Methods
The chat actor is a normal gedis actor that have only three actions/commands

- `session_new`: starts a new session for the a specific topic
- `work_report`: responsible for setting answers into chatbot session answers queue
- `work_get`: responsible for getting new questions from chatbot session questions queue

# How to create chatflow:

The chat flow is a python file that contains the questions and logic that build up the bot. To create a new chatflow 
into a package you need to create a new python file into the chatflows directory. The file name will be 
the name of topic used to access the chatbot from the browser:
(i.e. `food_get.py` => `http://localhost:8080/chat/food_get`)


The file contents must contains a method called `chat` that is been called by the gedis chatbot.
```python
def chat(bot):
    name = bot.string_ask("What's your name?")
```

You can use bot helper methods to generate questions:
- `string_ask`
- `int_ask`
- `text_ask`
- `password_ask`
- `multi_choice`
- `single_choice`
- `drop_down_choice`

You can also use two special helper methods which don't generate questions:
- `md_show`: can be used to send normal messages to the user in md format
- `redirect`: can be used to redirect the user to a specific url
