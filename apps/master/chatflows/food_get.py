def chat(bot):
    """
    to call this something like localhost:3000/bot/order_my_food will be called on webserver
    """

    food = bot.string_ask("What do you need to eat?")
    amount = bot.int_ask("Enter the amount you need to eat from %s in grams:" % food)
    sides = bot.multi_choice("Choose your side dishes: ", ['rice', 'fries', 'saute', 'smash potato'])
    print(sides)
    drink = bot.single_choice("Choose your Drink: ", ['tea', 'coffee', 'lemon'])
    print(drink)
    bot.md_show("#You have ordered: `%s` grams `%s`, with sides `%s`, and `%s` drink \
    ### Click next for the final step which will redirect you to threefold.me\
    " % (amount, food, sides, drink))
    bot.redirect("https://threefold.me")
