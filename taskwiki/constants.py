DEFAULT_VIEWPORT_VIRTUAL_TAGS = ("-DELETED", "-PARENT")
DEFAULT_SORT_ORDER = "status+,end+,due+,priority-,project+"

COMPLETION_DATE = """
    now
    yesterday today tomorrow
    later someday

    monday tuesday wednesday thursday friday saturday sunday

    january february march april may june july
    august september october november december

    sopd sod sond eopd eod eond
    sopw sow sonw eopw eow eonw
    sopww soww sonww eopww eoww eonww
    sopm som sonm eopm eom eonm
    sopq soq sonq eopq eoq eonq
    sopy soy sony eopy eoy eony

    goodfriday easter eastermonday ascension pentecost
    midsommar midsommarafton juhannus
""".split()

COMPLETION_RECUR = """
    daily day weekdays weekly biweekly fortnight monthly
    quarterly semiannual annual yearly biannual biyearly
""".split()
