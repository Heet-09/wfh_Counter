import streamlit as st
from datetime import date, timedelta, datetime
import math

# ----- UTILITY FUNCTIONS -----
def count_total_weekdays(start_date, end_date):
    current = start_date
    count = 0
    while current <= end_date:
        if current.weekday() < 5:
            count += 1
        current += timedelta(days=1)
    return count

def reducing_holidays_from_total_days(total_days, holidays):
    return total_days - sum(1 for h in holidays if h.weekday() < 5)

def days_work_from_office(total_days_without_holidays, percent):
    return total_days_without_holidays * percent

def date_exists(start_date, end_date, holidays):
    current = start_date
    weekday_holidays = 0
    while current <= end_date:
        if current.weekday() < 5 and current in holidays:
            weekday_holidays += 1
        current += timedelta(days=1)
    return weekday_holidays

def function_for_weekday_in_a_month_with_excluding_the_holidays(month, holidays, user_leaves):
    month_start_date = date(2025, month, 1)
    if month == 12:
        month_end_date = date(2026, 1, 1) - timedelta(days=1)
    else:
        month_end_date = date(2025, month + 1, 1) - timedelta(days=1)

    total_weekdays = count_total_weekdays(month_start_date, month_end_date)
    weekday_holidays = date_exists(month_start_date, month_end_date, holidays | user_leaves)
    return total_weekdays - weekday_holidays

# ----- MAIN APP -----
st.title("🏢 Work From Office Days Tracker")

# Initialize session state for leave dates and ranges
if "leave_days" not in st.session_state:
    st.session_state.leave_days = set()

if "leave_ranges" not in st.session_state:
    st.session_state.leave_ranges = []

if "temp_single_date" not in st.session_state:
    st.session_state.temp_single_date = date.today()

if "temp_range_start" not in st.session_state:
    st.session_state.temp_range_start = date.today()

if "temp_range_end" not in st.session_state:
    st.session_state.temp_range_end = date.today()

# --- Leave input UI ---
st.subheader("Add Leave Dates and Ranges")

# Single leave date input
single_date = st.date_input(
    "Pick a single leave date",
    value=st.session_state.temp_single_date,
    key="single_date_input"
)
st.session_state.temp_single_date = single_date

if st.button("Add Single Date"):
    st.session_state.leave_days.add(single_date)
    st.success(f"Added single leave date: {single_date}")

# Leave date range input
range_start = st.date_input(
    "Range start",
    value=st.session_state.temp_range_start,
    key="range_start_input"
)
range_end = st.date_input(
    "Range end",
    value=st.session_state.temp_range_end,
    key="range_end_input"
)
st.session_state.temp_range_start = range_start
st.session_state.temp_range_end = range_end

if st.button("Add Date Range"):
    if range_end >= range_start:
        st.session_state.leave_ranges.append((range_start, range_end))
        st.success(f"Added leave range: {range_start} to {range_end}")
    else:
        st.error("Range end date must be after or equal to start date.")

# Expand all ranges into individual leave dates
for start, end in st.session_state.leave_ranges:
    current = start
    while current <= end:
        st.session_state.leave_days.add(current)
        current += timedelta(days=1)

# Show all selected leave dates
st.subheader("All Selected Leave Dates:")
all_leave_dates = sorted(st.session_state.leave_days)
st.write(all_leave_dates)

# --- Other inputs ---
percent_input = st.number_input(
    "Enter % of total working days to work from office:",
    min_value=0.0, max_value=100.0, value=65.0
)
percentage_total_days_allowed = percent_input / 100

office_present_days = st.number_input(
    "Enter how many days you were already present in office:",
    min_value=0, value=88
)

# Static holidays for 2025
holidays = {
    date(2025, 1, 1), date(2025, 3, 14), date(2025, 4, 18), date(2025, 5, 1),
    date(2025, 8, 15), date(2025, 8, 27), date(2025, 10, 2),
    date(2025, 10, 21), date(2025, 10, 22), date(2025, 10, 23), date(2025, 12, 25),
}

start = date(2025, 1, 1)
end = date(2025, 12, 31)

total_weekdays = count_total_weekdays(start, end)
total_days_without_holidays = reducing_holidays_from_total_days(total_weekdays, holidays)
total_days_work_from_office = math.ceil(days_work_from_office(total_days_without_holidays, percentage_total_days_allowed))
days_needed_to_cover = total_days_work_from_office - office_present_days
current_month = datetime.now().month

availabe_days = {}
total_days_to_go = 0
for month in range(current_month, 13):
    avail = function_for_weekday_in_a_month_with_excluding_the_holidays(month, holidays, st.session_state.leave_days)
    availabe_days[month] = avail
    total_days_to_go += avail

months_left = 12 - current_month
days_per_month = math.ceil(days_needed_to_cover / months_left) if months_left > 0 else days_needed_to_cover

# — New part: Calculate available working days after holidays + leaves —
combined_holidays = holidays | st.session_state.leave_days

total_weekdays_excluding_all = 0
monthly_available_days = {}
for month in range(1, 13):
    month_start = date(2025, month, 1)
    if month == 12:
        month_end = date(2026, 1, 1) - timedelta(days=1)
    else:
        month_end = date(2025, month + 1, 1) - timedelta(days=1)

    total_weekdays_month = count_total_weekdays(month_start, month_end)
    holidays_in_month = sum(
        1 for d in combined_holidays if month_start <= d <= month_end and d.weekday() < 5
    )
    working_days_month = total_weekdays_month - holidays_in_month
    monthly_available_days[month] = working_days_month
    total_weekdays_excluding_all += working_days_month

# --- Outputs ---
st.subheader("📈 Summary:")
st.write("**Total weekdays (excluding weekends):**", total_weekdays)
st.write("**Total weekdays (excluding holidays):**", total_days_without_holidays)
st.write(f"**Work-from-office target ({percent_input}%):**", total_days_work_from_office)
st.write("**Office days already present:**", office_present_days)
st.write("**Days still needed to cover:**", max(0, days_needed_to_cover))
st.write("**Average days/month to reach goal:**", days_per_month)

st.subheader("🗓️ Working Days Available (After Holidays + Leaves):")
st.write(f"**Total available working days in 2025:** {total_weekdays_excluding_all}")
st.write("**Monthly available working days:**")
for m, days in monthly_available_days.items():
    month_name = date(2025, m, 1).strftime("%B")
    st.write(f"- {month_name}: {days} days")

st.subheader("📅 Available Days by Month (Adjusted):")
for m, days in availabe_days.items():
    month_name = date(2025, m, 1).strftime("%B")
    st.write(f"**{month_name}**: {days} office days → Must do: {max(0, days_per_month)} → Work from home: {days - days_per_month}")
