import streamlit as st

import pandas as pd

import math

import calendar

import altair as alt

import numpy as np

import datetime

 

# --- Function to calculate agent requirements ---

def calculate_agents(call_volume, avg_handle_time, occupancy, shrinkage, service_level):

    calls_per_hour = 3600 / avg_handle_time  # Calls an agent can handle per hour

    calls_per_shift = calls_per_hour * 7  # Assuming a 7-hour shift

    actual_calls_per_shift = calls_per_shift * occupancy  # Adjust for occupancy

 

    # Adjust agent requirement based on service level (higher SL = more agents)

    agents_no_shrinkage = math.ceil(call_volume / actual_calls_per_shift * (1 + (1 - service_level)))

   

    # Apply shrinkage

    agents_with_shrinkage = math.ceil(agents_no_shrinkage + (agents_no_shrinkage * shrinkage))

   

    return agents_no_shrinkage, agents_with_shrinkage

def calculate_service_level(call_volume, avg_handle_time, occupancy, shrinkage, num_agents):

    calls_per_hour = 3600 / avg_handle_time  # Calls an agent can handle per hour

    calls_per_shift = calls_per_hour * 7 * occupancy  # 7-hour shift adjusted for occupancy

   

    # Apply shrinkage to the number of agents

    effective_agents = num_agents * (1 - shrinkage)  # Adjust agent count for shrinkage

   

    # Calculate the maximum calls that can be handled

    max_calls_handled = effective_agents * calls_per_shift

   

    # Calculate service level

    service_level = max_calls_handled / call_volume

   

    # Ensure SL is capped at 100%

    service_level = min(service_level, 1)

 

    return service_level

 

# --- Function to calculate from CSV ---

def calculate_monthly_agents_from_csv(file_path, avg_handle_time, occupancy, shrinkage, service_level):

    df = pd.read_csv(file_path)

    df['Date'] = pd.to_datetime(df['Date'])

    agent_requirements = []

 

    for _, row in df.iterrows():

        call_volume = row['Forecasted Call Volume']

        agents_no_shrinkage, agents_with_shrinkage = calculate_agents(call_volume, avg_handle_time, occupancy, shrinkage, service_level)

       

        agent_requirements.append({

            "Date": row['Date'],

            "Day": row['Day'],

            "Forecasted Call Volume": call_volume,

            "Agents (No Shrinkage)": agents_no_shrinkage,

            "Agents (With Shrinkage)": agents_with_shrinkage

        })

 

    return pd.DataFrame(agent_requirements)

 

# --- Calendar View Functions ---

def generate_calendar_view(agent_data, selected_month):

    cal = calendar.Calendar()

    first_date = agent_data['Date'].min()

    last_date = agent_data['Date'].max()

 

    selected_month_data = agent_data[agent_data['Date'].dt.month == selected_month]

    selected_month_data = selected_month_data.set_index('Date')

 

    month = selected_month

    year = first_date.year if selected_month >= first_date.month else last_date.year

 

    calendar_grid = []

    for week in cal.monthdayscalendar(year, month):

        week_row = []

        for day in week:

            if day == 0:

                week_row.append("")

            else:

                date_full = pd.Timestamp(day=day, month=month, year=year)

                if date_full in selected_month_data.index:

                    agents = selected_month_data.loc[date_full, 'Agents (With Shrinkage)']

                    forecasted_calls = selected_month_data.loc[date_full, 'Forecasted Call Volume']

                    formatted_date = date_full.strftime('%d-%m-%Y')

 

                    week_row.append(

                        f"<div style='background-color:white; padding:10px; border:1px solid #ddd; width:120px;'>"

                        f"<span style='color:blue; font-size:18px; font-weight:bold;'>{agents}</span><br>"

                        f"<span style='font-size:16px; color:black;'>{forecasted_calls:,.0f}</span><br>"

                        f"<span style='font-size:12px; color:gray;'>{formatted_date}</span></div>"

                    )

                else:

                    week_row.append(

                        f"<div style='background-color:white; padding:10px; border:1px solid #ddd; width:120px;'>"

                        f"<span style='color:red; font-size:18px;'>N/A</span></div>"

                    )

        calendar_grid.append(week_row)

 

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    calendar_df = pd.DataFrame(calendar_grid, columns=days)

 

    return calendar_df

 

def display_calendar(calendar_df):

    styled_calendar = calendar_df.style.set_properties(**{

        'text-align': 'center',

        'background-color': 'white',

        'border': '1px solid #ddd',

        'padding': '10px',

        'font-family': 'Arial, sans-serif'

    }).set_table_styles([{

        'selector': 'th',

        'props': [('background-color', '#4682B4'),

                  ('color', 'white'),

                  ('text-align', 'center'),

                  ('padding', '10px')]},

    ])

    st.write(styled_calendar.to_html(), unsafe_allow_html=True)

 

# --- Visualization ---

def plot_agents_per_day(agent_data, selected_month):

    monthly_agents = agent_data[agent_data['Date'].dt.month == selected_month]

    monthly_agents['Day'] = monthly_agents['Date'].dt.day

 

    base_chart = alt.Chart(monthly_agents).mark_bar().encode(

        x=alt.X('Day:O', title='Day of the Month', axis=alt.Axis(labelAngle=360)),

        y=alt.Y('Agents (With Shrinkage):Q', title='Agents Required'),

        color=alt.Color('Agents (With Shrinkage):Q', scale=alt.Scale(scheme='blues')),

        tooltip=['Date:T', 'Agents (With Shrinkage):Q']

    )

 

    text = base_chart.mark_text(

        align='center',

        baseline='middle',

        dy=-5,

        color='brown'

    ).encode(

        text=alt.Text('Agents (With Shrinkage):Q', format='.0f')

    )

 

    chart = (base_chart + text).properties(

        title=f'Agent Requirements for {calendar.month_name[selected_month]}',

        width=600,

        height=600

    )

 

    st.altair_chart(chart, use_container_width=True)

import numpy as np

 

def generate_hourly_distribution(total_calls, day_of_week, random_variation=0.05):

    """

    Generates a realistic hourly call distribution for Karachi, Pakistan,

    with distinct profiles for each weekday and slight random variation.

   

    Arguments:

        total_calls (int): Total calls forecasted for the day.

        day_of_week (int): Monday=0, Tuesday=1, ..., Sunday=6.

        random_variation (float): e.g. 0.05 => ±5% random variation to each hour.

 

    Notes:

        - Very low volume at midnight/early morning

        - Sharp increase after ~10:00

        - Decrease again after ~21:00

        - Friday includes a midday dip, but less drastic

        - We add random variation to keep the curve from looking overly "perfect."

    """

 

    # ----------------- MONDAY -----------------

    monday_profile = [

        0.004, 0.003, 0.002, 0.002, 0.002, 0.002,  # 00:00 - 05:00 extremely low

        0.003, 0.005, 0.010, 0.020, 0.055, 0.065,  # 06:00 - 11:00 ramping up

        0.075, 0.080, 0.080, 0.075, 0.060, 0.050,  # 12:00 - 17:00 midday peak

        0.045, 0.040, 0.030, 0.020, 0.015, 0.010   # 18:00 - 23:00 gradual drop

    ]

 

    # ----------------- TUESDAY -----------------

    tuesday_profile = [

        0.003, 0.002, 0.002, 0.002, 0.002, 0.003,

        0.004, 0.007, 0.012, 0.022, 0.060, 0.070,

        0.075, 0.080, 0.080, 0.070, 0.065, 0.055,

        0.045, 0.040, 0.030, 0.025, 0.015, 0.010

    ]

 

    # ----------------- WEDNESDAY -----------------

    wednesday_profile = [

        0.005, 0.003, 0.002, 0.002, 0.002, 0.003,

        0.005, 0.008, 0.013, 0.025, 0.058, 0.068,

        0.075, 0.080, 0.078, 0.070, 0.065, 0.055,

        0.050, 0.040, 0.035, 0.025, 0.015, 0.010

    ]

 

    # ----------------- THURSDAY -----------------

    thursday_profile = [

        0.004, 0.003, 0.002, 0.002, 0.002, 0.003,

        0.005, 0.008, 0.016, 0.030, 0.060, 0.070,

        0.075, 0.080, 0.075, 0.070, 0.065, 0.055,

        0.050, 0.040, 0.035, 0.025, 0.015, 0.010

    ]

 

    # ----------------- FRIDAY -----------------

    # Less severe dip at 1–2 PM to avoid unrealistically plummeting from 2500 calls to just a few hundred

    friday_profile = [

        0.004, 0.003, 0.002, 0.002, 0.002, 0.003,

        0.005, 0.009, 0.016, 0.030, 0.060, 0.070,

        0.075, 0.030, 0.035, 0.045, 0.065, 0.055,

        0.050, 0.040, 0.035, 0.025, 0.015, 0.010

    ]

 

    # ----------------- SATURDAY -----------------

    saturday_profile = [

        0.006, 0.004, 0.003, 0.003, 0.003, 0.004,

        0.006, 0.010, 0.018, 0.040, 0.065, 0.070,

        0.075, 0.080, 0.075, 0.070, 0.060, 0.055,

        0.050, 0.045, 0.030, 0.020, 0.015, 0.010

    ]

 

    # ----------------- SUNDAY -----------------

    sunday_profile = [

        0.010, 0.007, 0.005, 0.004, 0.003, 0.003,

        0.005, 0.010, 0.020, 0.040, 0.060, 0.070,

        0.075, 0.080, 0.075, 0.070, 0.060, 0.055,

        0.050, 0.045, 0.035, 0.025, 0.015, 0.010

    ]

 

    # Map day_of_week -> daily distribution

    profiles = {

        0: monday_profile,    # Monday

        1: tuesday_profile,   # Tuesday

        2: wednesday_profile, # Wednesday

        3: thursday_profile,  # Thursday

        4: friday_profile,    # Friday

        5: saturday_profile,  # Saturday

        6: sunday_profile     # Sunday

    }

 

    # Choose the profile for this weekday, or default to Monday

    profile_arr = np.array(profiles.get(day_of_week, monday_profile))

 

    # (1) Introduce small random variation so it doesn't look too “perfect.”

    # For each hour, multiply by a random factor in [1 - random_variation, 1 + random_variation].

    # Example: ±5% => random_variation=0.05

    variation_factors = np.random.uniform(

        1 - random_variation,

        1 + random_variation,

        size=len(profile_arr)

    )

    profile_arr = profile_arr * variation_factors

 

    # (2) Normalize so the total sums to 1 again

    total_pct = profile_arr.sum()

    profile_arr = profile_arr / total_pct

 

    # (3) Scale to total calls (rounded integer per hour)

    hourly_calls = np.round(profile_arr * total_calls).astype(int)

 

    # Ensure exactly 24 entries

    if len(hourly_calls) < 24:

        hourly_calls = np.pad(hourly_calls, (0, 24 - len(hourly_calls)), mode='constant')

    elif len(hourly_calls) > 24:

        hourly_calls = hourly_calls[:24]

 

    return hourly_calls

 

def plot_hourly_distribution(hourly_calls, selected_date):

    hours = range(24)

    df = pd.DataFrame({'Hour': hours, 'Calls': hourly_calls})

 

    # Base bar chart

    bar_chart = alt.Chart(df).mark_bar().encode(

        x=alt.X('Hour:O', title='Hour of Day', axis=alt.Axis(labelAngle=360)),

        y=alt.Y('Calls:Q', title='Number of Calls'),

        tooltip=['Hour:O', 'Calls:Q']

    ).properties(

        title=f'Hourly Call Distribution for {selected_date}',

        width=600,

        height=400

    )

 

    # Data labels (text over bars)

    text_labels = alt.Chart(df).mark_text(

        align='center',

        baseline='middle',

        dy=-10,  # Adjust position (above the bar)

        color='white'

    ).encode(

        x=alt.X('Hour:O'),

        y=alt.Y('Calls:Q'),

        text=alt.Text('Calls:Q')  # Display the value of calls

    )

 

    # Combine the bar chart and the data labels

    final_chart = bar_chart + text_labels

 

    # Render the chart in Streamlit

    st.altair_chart(final_chart, use_container_width=True)




# --- Reverse Calculation (Calls Handled by Agents) ---

def calculate_calls_by_agents(num_agents, avg_handle_time, occupancy, shrinkage, service_level):

    calls_per_hour = 3600 / avg_handle_time  # Calls an agent can handle per hour

    calls_per_shift = calls_per_hour * 7 * occupancy  # 7-hour shift adjusted for occupancy

 

    # Apply shrinkage to the number of agents

    effective_agents = num_agents * (1 - shrinkage)  # Adjust agent count for shrinkage

 

    # Calculate maximum calls handled with adjusted agent count

    max_calls_handled = int(effective_agents * calls_per_shift / (1 + (1 - service_level)))

 

    return max_calls_handled

 

# --- Main App ---

def main():

    st.title("Call Center Staffing Calculator")

    st.markdown("Estimate the number of agents required to handle calls over different timeframes and visualize monthly forecasts in a clean calendar view.")

   

    # Sidebar navigation

    st.sidebar.image("ubl-united-bank-limited-logo-png-transparent.png")

    mode = st.sidebar.radio("Select Mode", ["Agent Requirement", "Calls Handled By Agent", "Service Level"])

 

   

    # Common Inputs

    avg_handle_time = st.number_input("Avg Handle Time (seconds)", min_value=1, value=300, key="sl_avg_handle_time")

 

    occupancy = st.slider("Occupancy (%)", 50, 100, 85) / 100

    shrinkage = st.slider("Shrinkage (%)", 0, 100, 20) / 100

   

    if mode in ["Agent Requirement", "Calls Handled By Agent"]:

        service_level = st.slider("Service Level (%)", 50, 100, 90) / 100

    if mode == "Agent Requirement":

        file_upload = st.file_uploader("📂 Upload Forecasted Call Volume CSV", type=['csv'])

       

        if file_upload:

            agent_data = calculate_monthly_agents_from_csv(file_upload, avg_handle_time, occupancy, shrinkage, service_level)

            available_months = agent_data['Date'].dt.month.unique()

            selected_month = st.selectbox("Select Month", options=available_months, format_func=lambda x: calendar.month_name[x])

 

            if st.button("Generate Monthly Forecast"):

                selected_month_data = agent_data[agent_data['Date'].dt.month == selected_month]

                selected_month_data['Formatted Date'] = selected_month_data['Date'].dt.date

 

                st.subheader(f"Daily Agent Requirements for {calendar.month_name[selected_month]}")

                st.dataframe(selected_month_data[['Formatted Date', 'Day', 'Forecasted Call Volume', 'Agents (No Shrinkage)', 'Agents (With Shrinkage)']])

 

                st.subheader(f"Calendar View for {calendar.month_name[selected_month]}")

                calendar_df = generate_calendar_view(selected_month_data, selected_month)

                display_calendar(calendar_df)

 

                st.subheader(f"Agent Requirements Over Time for {calendar.month_name[selected_month]}")

                plot_agents_per_day(selected_month_data, selected_month)

 

            # Hourly Distribution

            st.subheader("Hourly Call Distribution")

            selected_date_str = st.date_input("Select Date for Hourly Distribution", min_value=agent_data['Date'].min().date(), max_value=agent_data['Date'].max().date())

            selected_date = pd.to_datetime(selected_date_str)

 

            daily_data = agent_data[agent_data['Date'] == selected_date]

 

            if not daily_data.empty:

                total_calls = daily_data['Forecasted Call Volume'].values[0]

 

                # Determine if it's Friday

                # is_friday = selected_date.weekday() == 4  # Monday=0, ..., Friday=4

 

                # hourly_calls = generate_hourly_distribution(total_calls, is_friday)

                day_of_week = selected_date.weekday()  # Monday=0, Tuesday=1, ...

                hourly_calls = generate_hourly_distribution(total_calls, day_of_week)

 

                plot_hourly_distribution(hourly_calls, selected_date_str)

            else:

                st.warning("No data available for the selected date.")

 

    elif mode == "Calls Handled By Agent":

        st.subheader("🔄 Calls Handled by Agents")

        num_agents = st.number_input("Number of Agents Available", min_value=1, value=50, key="sl_num_agents")

 

       

        if st.button("Calculate Calls Handled"):

            calls_handled = calculate_calls_by_agents(num_agents, avg_handle_time, occupancy, shrinkage, service_level)

            st.success(f"📞 These {num_agents} agents can handle approximately **{calls_handled} calls per day**.")

   

    elif mode == "Service Level":

        st.subheader("📊 Calculate Service Level")

   

        call_volume = st.number_input("Total Forecasted Calls", min_value=1, value=1000, key="service_level_call_volume")

        num_agents = st.number_input("Number of Agents Available", min_value=1, value=50, key="service_level_num_agents")

 

        if st.button("Calculate Service Level", key="sl_calculate_button"):

            service_level = calculate_service_level(call_volume, avg_handle_time, occupancy, shrinkage, num_agents)

            lower_bound = max(0, service_level - 0.02)  # Ensure not below 0%

            upper_bound = min(1, service_level + 0.02)  # Ensure not above 100%

 

            st.info(f"✅ Expected Service Level Range: **{lower_bound*100:.2f}% - {upper_bound*100:.2f}%**")

 

if __name__ == "__main__":

    main()