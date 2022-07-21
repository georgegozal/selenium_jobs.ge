from jobs.jobs import Jobs

# args to inculde
args1 = [
    'Python','Back','ბექი'
]

# args to exclude
args2 = [
    'Java',
]
#TODO: დაამატე დედლაინამდე დარჩენილი დღეები
try:
    with Jobs() as bot:
        bot.land_first_page()
        bot.change_category()
        bot.report(
            # args1=input('შეიყვანე სასურველი სიტყვები რასაც უნდა შეიცავდეს სათაური \nგამოყავით მძიმით ან ინტერვალით').strip().split(',').split(),
            # args2=input('შეიყვანე სასურველი სიტყვები რაც არ უნდა იყოს სათაურში \nგამოყავით მძიმით ან ინტერვალით').strip().split(',').split()
args1,
args2
            )

except Exception as e:
    print(e)