from jobs.jobs import Jobs

# args to inculde
args1 = [
    'Python','Back','ბექი'
]

# args to exclude
args2 = [
    'Java',
]

try:
    with Jobs(teardown=False) as bot:
        bot.land_first_page()
        bot.change_category()
        bot.report(args1,args2)

except Exception as e:
    print(e)