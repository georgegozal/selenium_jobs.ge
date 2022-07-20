from jobs.jobs import Jobs

try:
    with Jobs(teardown=False) as bot:
        bot.land_first_page()
        bot.change_category()
        # bot.get_table_rows()
        bot.get_data_from_rows()

except Exception as e:
    print(e)