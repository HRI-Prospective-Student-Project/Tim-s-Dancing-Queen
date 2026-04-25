import pandas as pd
import re

def aggregate():
    print("Combining logs and interaction responses...")
    # Load data
    # delimiter="|" handles the Misty log format
    log = pd.read_csv('misty_interactions.log', delimiter="|", names=["Tag", "Action", "Page", "Details"])
    interactions = pd.read_csv("Interaction Log(Responses).csv")

    # 1. Convert columns to actual datetime objects
    log["Timestamp"] = pd.to_datetime(log["Tag"].str.split(" - ").str[0].str.strip())    
    interactions["Start"] = pd.to_datetime(interactions["Start"])
    interactions["End"] = pd.to_datetime(interactions["End"])

    # Initialize columns
    log["Participants"] = ""
    log["ID"] = 0

    # 2. Match logs to interactions with a SLACK BUFFER
    # This accounts for Gemini API latency (logs appearing a few seconds late)
    slack = pd.Timedelta(seconds=30)

    for int_row in interactions.itertuples():
        # Mask: Timestamp is between (Start - slack) and (End + slack)
        mask = (log["Timestamp"] >= (int_row.Start - slack)) & \
               (log["Timestamp"] <= (int_row.End + slack))
        
        log.loc[mask, "ID"] = int_row.ID
        log.loc[mask, "Participants"] = int_row.Count 

    # Save temporary combined file
    log.to_csv("Data.csv", index=False)

def standardize_combined_file(df):
    print("Starting robust standardization...")
    df.columns = df.columns.str.strip()

    # 1. IDENTIFY GEMINI ROWS
    gemini_mask = df["Tag"].str.contains("GEMINI", na=False) | \
                  df["Action"].str.contains("GEMINI", na=False)
    
    print(f"Found {gemini_mask.sum()} Gemini rows.")

    # 2. FIX GEMINI CONTENT
    if gemini_mask.any():
        # Move dialogue to Details and standardize Action/Page
        df.loc[gemini_mask, "Details"] = df.loc[gemini_mask, "Action"]
        df.loc[gemini_mask, "Action"] = "GEMINI_IO"
        df.loc[gemini_mask, "Page"] = "/home"

    # 3. ROBUST SESSION ID RECOVERY
    # Extract existing session IDs (sess-xxxx) into a helper column
    df['session_id'] = df['Tag'].str.extract(r'(sess-\w+)')
    
    # ffill() propagates the session ID from the last navigation row down to Gemini rows
    df['session_id'] = df['session_id'].ffill().bfill()

    # 4. RECONSTRUCT TAGS
    # We extract just the timestamp part and re-attach the recovered session ID
    df['temp_ts'] = df['Tag'].str.extract(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})')
    df['Tag'] = df['temp_ts'] + " - ID: " + df['session_id']

    # 5. REMOVE BUMPER PRESSES
    # We do this now that session IDs have been filled
    bumper_mask = df["Tag"].str.contains("BUMPER_PRESS", na=False) | \
                  df["Action"].str.contains("BUMPER_PRESS", na=False)
    print(f"Removing {bumper_mask.sum()} Bumper Press rows...")
    df = df[~bumper_mask]

    # Cleanup helper columns
    df = df.drop(columns=["temp_ts", "session_id"])
    return df

if __name__ == "__main__":
    try:
        # Step 1: Combine the files and assign initial IDs
        aggregate()
        
        # Step 2: Load for cleaning
        combined_df = pd.read_csv("Data.csv")
        
        # Step 3: Standardize labels and fill missing session strings
        combined_df = standardize_combined_file(combined_df)
        
        # Step 4: Remove ID = 0 (rows that didn't fit any session window)
        before_count = len(combined_df)
        combined_df = combined_df[combined_df["ID"] != 0]
        after_count = len(combined_df)
        
        print(f"Filtered out {before_count - after_count} rows with ID=0.")
        
        # Step 5: Final Save
        combined_df.to_csv("Data.csv", index=False)
        print("Success! Data.csv is now standardized, bridged, and filtered.")
        
    except Exception as e:
        print(f"An error occurred: {e}")