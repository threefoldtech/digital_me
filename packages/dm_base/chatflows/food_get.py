from Jumpscale import j
#THIS IS A TEST CHAT

def chat(bot):
    """
    to call http://localhost:5050/chat/session/food_get
    """

    res={}
    food = bot.string_ask("What do you need to eat?")
    amount = bot.int_ask("Enter the amount you need to eat from %s in grams:" % food)
    sides = bot.multi_choice("Choose your side dishes: ", ['rice', 'fries', 'saute', 'smash potato'])
    drink = bot.single_choice("Choose your Drink: ", ['tea', 'coffee', 'lemon'])


    R = """
    # You have ordered: 
    
    - {{amount}} grams, with sides {{sides}} and {{drink}} drink

    ### Click next 
    
    for the final step which will redirect you to threefold.me


    """

    R2 = j.tools.jinja2.text_render(j.core.text.strip(R),**locals())

    bot.md_show(R2)

    bot.redirect("https://threefold.me")
