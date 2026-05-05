import streamlit as st
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Weather Dashboard",
    page_icon="🌤️",
    layout="wide"
)

st.title("🌤️ Live Weather Dashboard")
st.markdown("Real-time weather data and 5-day forecast "
            "for any city in the world.")
st.markdown("---")

# API key
API_KEY = "aef0d82db3dbfbbbab87e896a879c3b3"

if not API_KEY:
    st.warning("⚠️ Add your OpenWeatherMap API key "
               "to .streamlit/secrets.toml")
    API_KEY = st.text_input(
        "Enter API key temporarily:",
        type="password",
        placeholder="aef0d82db3dbfbbbab87e896a879c3b3"
    )

# Weather functions
def get_current_weather(city, api_key):
    url = (f"https://api.openweathermap.org/data/2.5/"
           f"weather?q={city}&appid={api_key}"
           f"&units=metric")
    response = requests.get(url)
    return response.json()

def get_forecast(city, api_key):
    url = (f"https://api.openweathermap.org/data/2.5/"
           f"forecast?q={city}&appid={api_key}"
           f"&units=metric")
    response = requests.get(url)
    return response.json()

def get_weather_emoji(desc):
    desc = desc.lower()
    if 'clear'      in desc: return '☀️'
    if 'cloud'      in desc: return '☁️'
    if 'rain'       in desc: return '🌧️'
    if 'drizzle'    in desc: return '🌦️'
    if 'thunder'    in desc: return '⛈️'
    if 'snow'       in desc: return '❄️'
    if 'mist'       in desc: return '🌫️'
    if 'haze'       in desc: return '🌫️'
    return '🌤️'

# Sidebar
st.sidebar.header("🔍 Search City")

# Quick cities
quick_cities = [
    "Bhubaneswar", "Mumbai", "Delhi",
    "Bangalore", "Chennai", "Kolkata",
    "London", "New York", "Tokyo",
    "Dubai", "Singapore", "Sydney"
]

selected_quick = st.sidebar.selectbox(
    "Quick select:", ["Custom..."] + quick_cities)

if selected_quick == "Custom...":
    city = st.sidebar.text_input(
        "Enter city name:",
        placeholder="e.g. Paris, Tokyo"
    )
else:
    city = selected_quick

unit_label = "°C"

if st.sidebar.button("🔍 Get Weather",
                     type="primary") or city:

    if not city:
        st.info("👈 Select or enter a city to get started.")
        st.stop()

    if not API_KEY:
        st.error("Please enter your API key.")
        st.stop()

    with st.spinner(f"Fetching weather for {city}..."):
        current  = get_current_weather(city, API_KEY)
        forecast = get_forecast(city, API_KEY)

    if current.get('cod') != 200:
        st.error(f"City not found: {city}. "
                 f"Try another name.")
        st.stop()

    # Current weather data
    temp       = current['main']['temp']
    feels_like = current['main']['feels_like']
    humidity   = current['main']['humidity']
    pressure   = current['main']['pressure']
    wind_speed = current['wind']['speed']
    visibility = current.get('visibility', 0) / 1000
    desc       = current['weather'][0]['description']
    emoji      = get_weather_emoji(desc)
    country    = current['sys']['country']
    sunrise    = datetime.fromtimestamp(
        current['sys']['sunrise'])
    sunset     = datetime.fromtimestamp(
        current['sys']['sunset'])
    temp_min   = current['main']['temp_min']
    temp_max   = current['main']['temp_max']

    # Header
    st.markdown(
        f"<h2 style='text-align:center'>"
        f"{emoji} {city.title()}, {country}"
        f"</h2>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<h1 style='text-align:center; "
        f"color:#f39c12'>{temp:.1f}{unit_label}</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<p style='text-align:center; color:gray'>"
        f"{desc.title()} | "
        f"Feels like {feels_like:.1f}{unit_label}</p>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    # Metrics row
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("💧 Humidity",    f"{humidity}%")
    c2.metric("💨 Wind",        f"{wind_speed} m/s")
    c3.metric("🌡️ Min",         f"{temp_min:.1f}°C")
    c4.metric("🌡️ Max",         f"{temp_max:.1f}°C")
    c5.metric("👁️ Visibility",  f"{visibility:.1f} km")
    c6.metric("📊 Pressure",    f"{pressure} hPa")

    st.markdown("---")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### ☀️ Sun Schedule")
        s1, s2 = st.columns(2)
        s1.metric("Sunrise", sunrise.strftime('%H:%M'))
        s2.metric("Sunset",  sunset.strftime('%H:%M'))

        daylight = sunset - sunrise
        hours    = int(daylight.seconds / 3600)
        minutes  = int((daylight.seconds % 3600) / 60)
        st.metric("Daylight", f"{hours}h {minutes}m")

        st.markdown("### 🌡️ Temperature Gauge")
        fig_g, ax_g = plt.subplots(figsize=(5, 3))
        ax_g.barh(['Today'],
                  [temp_max - temp_min],
                  left=[temp_min],
                  color='#f39c12',
                  height=0.4,
                  alpha=0.8)
        ax_g.axvline(x=temp, color='#e74c3c',
                     linewidth=2.5,
                     label=f'Now: {temp:.1f}°C')
        ax_g.set_title("Today's Temperature Range",
                       fontsize=11)
        ax_g.set_xlabel("Temperature (°C)")
        ax_g.legend(fontsize=9)
        plt.tight_layout()
        st.pyplot(fig_g)

    with col2:
        # 5-day forecast
        st.markdown("### 📅 5-Day Forecast")

        if forecast.get('cod') == '200':
            fc_list = forecast['list']
            fc_df   = pd.DataFrame([{
                'datetime': datetime.fromtimestamp(
                    item['dt']),
                'temp':     item['main']['temp'],
                'feels':    item['main']['feels_like'],
                'humidity': item['main']['humidity'],
                'desc':     item['weather'][0]
                            ['description'],
                'wind':     item['wind']['speed']
            } for item in fc_list])

            # Temperature forecast chart
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(fc_df['datetime'], fc_df['temp'],
                    color='#e74c3c', linewidth=2,
                    marker='o', markersize=4,
                    label='Temperature')
            ax.fill_between(
                fc_df['datetime'],
                fc_df['temp'],
                fc_df['temp'].min() - 2,
                alpha=0.15, color='#e74c3c'
            )
            ax.plot(fc_df['datetime'],
                    fc_df['humidity'],
                    color='#3498db',
                    linewidth=1.5,
                    linestyle='--',
                    label='Humidity %',
                    alpha=0.7)
            ax.set_title(
                f'5-Day Temperature & Humidity — '
                f'{city.title()}',
                fontsize=13
            )
            ax.set_ylabel('Temperature (°C) / '
                          'Humidity (%)')
            ax.legend(fontsize=10)
            ax.grid(alpha=0.3)
            ax.xaxis.set_major_formatter(
                mdates.DateFormatter('%d %b %H:%M'))
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            st.pyplot(fig)

    # Daily summary cards
    st.markdown("---")
    st.markdown("### 📆 Daily Summary")

    if forecast.get('cod') == '200':
        fc_df['date'] = fc_df['datetime'].dt.date
        daily_fc      = fc_df.groupby('date').agg(
            max_temp=('temp', 'max'),
            min_temp=('temp', 'min'),
            avg_humidity=('humidity', 'mean'),
            desc=('desc', 'first')
        ).reset_index()

        cols = st.columns(min(5, len(daily_fc)))
        for i, (_, row) in enumerate(
            daily_fc.head(5).iterrows()
        ):
            with cols[i]:
                day_name = pd.Timestamp(
                    row['date']).strftime('%a\n%d %b')
                emoji_d  = get_weather_emoji(row['desc'])
                st.markdown(
                    f"<div style='text-align:center; "
                    f"padding:10px; border-radius:10px; "
                    f"background:#1e1e2e'>"
                    f"<b>{day_name}</b><br>"
                    f"<span style='font-size:2em'>"
                    f"{emoji_d}</span><br>"
                    f"<b style='color:#e74c3c'>"
                    f"{row['max_temp']:.0f}°</b> / "
                    f"<span style='color:#3498db'>"
                    f"{row['min_temp']:.0f}°</span><br>"
                    f"<small>{row['desc'].title()}"
                    f"</small>"
                    f"</div>",
                    unsafe_allow_html=True
                )

    # Compare cities
    st.markdown("---")
    st.markdown("### ⚖️ Compare Cities")
    compare_input = st.text_input(
        "Enter cities to compare "
        "(comma separated):",
        value="Mumbai, Delhi, Bangalore, Chennai"
    )

    if st.button("Compare Weather", type="primary"):
        cities_list = [c.strip()
                       for c in compare_input.split(',')]
        compare_data = []

        for c in cities_list[:6]:
            try:
                data = get_current_weather(c, API_KEY)
                if data.get('cod') == 200:
                    compare_data.append({
                        'City':      c.title(),
                        'Temp (°C)': round(
                            data['main']['temp'], 1),
                        'Humidity':  data['main']
                                     ['humidity'],
                        'Wind (m/s)':data['wind']
                                     ['speed'],
                        'Condition': data['weather'][0]
                                     ['description']
                                     .title()
                    })
            except:
                pass

        if compare_data:
            df_c = pd.DataFrame(compare_data)
            st.dataframe(df_c,
                         use_container_width=True,
                         hide_index=True)

            fig_c, axes = plt.subplots(
                1, 2, figsize=(12, 4))
            colors = ['#e74c3c', '#3498db',
                      '#2ecc71', '#f39c12',
                      '#9b59b6', '#1abc9c']

            axes[0].bar(df_c['City'],
                        df_c['Temp (°C)'],
                        color=colors[:len(df_c)],
                        edgecolor='black')
            axes[0].set_title('Temperature Comparison',
                              fontsize=12)
            axes[0].set_ylabel('Temperature (°C)')
            plt.setp(axes[0].xaxis.get_majorticklabels(),
                     rotation=30)

            axes[1].bar(df_c['City'],
                        df_c['Humidity'],
                        color=colors[:len(df_c)],
                        edgecolor='black')
            axes[1].set_title('Humidity Comparison',
                              fontsize=12)
            axes[1].set_ylabel('Humidity (%)')
            plt.setp(axes[1].xaxis.get_majorticklabels(),
                     rotation=30)

            plt.tight_layout()
            st.pyplot(fig_c)

else:
    st.info("👈 Select a city from the sidebar "
            "to see live weather data.")

st.markdown("---")
st.markdown(
    "Built by **Jyotiraditya** | "
    "Powered by OpenWeatherMap API | "
    "Live data updated every request"
)