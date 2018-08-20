from jumpscale import j


def chat(bot):
    """
    to call http://localhost:5050/chat/session/me_auth
    """
    dm_table = j.servers.gedis.latest.bcdb.table_get("dm_myself")
    if not dm_table.db.count:
        bot.md_show("It seems this is your first time configuration, click next to register your data")
        email = bot.string_ask("Enter your email?")
        secret = bot.string_ask("Enter your password?")
        dm_table.set(data={"email": [email], "secret": secret})
    else:
        trials = 0
        max_trials = 3
        while trials < max_trials:
            email = bot.string_ask("Enter your email?")
            secret = bot.string_ask("Enter your password?")
            user_id = dm_table.db.list()[0]
            user = dm_table.get(user_id)
            if secret == user.secret:
                logged_user = User()
                logged_user.id = user.id
                bot.q_out.put({
                    "cat": "login",
                    "user": logged_user
                })
                break
            else:
                trials += 1
                bot.md_show("wrong user or password, please try again")
                continue
        else:
            bot.md_show("wrong user or password, you exceeded your number of trials")
