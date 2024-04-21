import pandas as pd
import json
import matplotlib.pyplot as plt
import streamlit as st

# Assuming your JSON data is stored in a file named 'data.json'
with open('blockchain.json', 'r') as file:
    data = json.load(file)

# Convert the 'data' field from string to list of tuples
for item in data:
    item['data'] = eval(item['data'])

# Create DataFrame
df = pd.DataFrame(data)

# Drope the 1st row as it is a Genesis Block
df.drop(index=0)

# Create New DataFrame for ploting
new_df = df[['index', 'timestamp', 'data']]
new_df.set_index('index', inplace= True)

# Function to sum positive and negative values separately
def sum_pos_neg(row):
    positive_sum = 0
    negative_sum = 0
    for entry in row:
        entry = eval(entry)
        positive_sum += float(entry[1])
        negative_sum += float(entry[2])
    return positive_sum, negative_sum

# Apply function to each row and store results in new columns
new_df[['Consumed', 'Produced']] = new_df['data'].apply(sum_pos_neg).apply(pd.Series)

new_df['Produced'] = new_df['Produced'].abs()

new_df['timestamp'] = pd.to_datetime(new_df['timestamp'])

# Convert timestamp column to datetime and apply format function using lambda
new_df['timestamp'] = new_df['timestamp'].apply(lambda x: pd.to_datetime(x).strftime('%Y-%m-%d %H:%M:%S'))

# new_df.drop('data', axis=1)

# Plotting
st.set_option('deprecation.showPyplotGlobalUse', False)

st.title('Consumed vs Produced')

# Select which data to plot
plot_data = st.multiselect('Select data to plot', ['Consumed', 'Produced'])

if len(plot_data) > 0:
    plt.figure(figsize=(10, 6))
    for col in plot_data:
        plt.plot(new_df['timestamp'], new_df[col], label=col)
    
    plt.xlabel('Timestamp')
    plt.ylabel('Value')
    plt.title('Consumed vs Produced')
    plt.legend()

    # Rotate x-labels by 90 degrees
    plt.xticks(rotation=90)
    
    st.pyplot()
else:
    st.write('Please select at least one data to plot')


# Define the hash value you're interested in
desired_hash = st.text_input("Enter the hash")
host = st.text_input("Enter the host")

# Function to find data based on hash and host
def find_data(df, desired_hash, host):
    result = df[df['hash'] == desired_hash]
    if not result.empty:
        data = result['data'].iloc[0]
        for entry in data:
            entry = eval(entry)
            if host == entry[0]:
                return entry[0], entry[1], entry[2]
    return None, None, None

# Call the function to get data
host_result, consumption_result, production_result = find_data(df, desired_hash, host)

# Display the result
if host_result is not None:
    st.write(f'Host: {host_result}')
    st.write(f'Consumption: {consumption_result}')
    st.write(f'Production: {production_result}')
else:
    st.write("No data found for the given hash.")

