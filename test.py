import datetime

# Dates as strings
date1_str = "07-12-2024"
date2_str = "01-01-2025"

# Parse the strings into datetime objects
date1 = datetime.datetime.strptime("07-12-2024", "%d-%m-%Y").date()
date2 = datetime.datetime.strptime("01-01-2025", "%d-%m-%Y").date()

# Compare the dates
if date1 < date2:
    print(f"{date1_str} is earlier than {date2_str}")
elif date1 > date2:
    print(f"{date1_str} is later than {date2_str}")
else:
    print(f"{date1_str} is the same as {date2_str}")
