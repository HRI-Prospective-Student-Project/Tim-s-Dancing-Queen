import pandas as pd

def aggregate():
    # Load data
    # delimiter="|" handles the Misty log format
    log = pd.read_csv('misty_interactions.log', delimiter="|", names=["Tag", "Action", "Page", "Details"])
    interactions = pd.read_csv("Interaction Log(Responses).csv")

    # 1. Convert columns to actual datetime objects
    # We strip spaces to ensure the split works perfectly
    log["Timestamp"] = pd.to_datetime(log["Tag"].str.split(" - ").str[0].str.strip())    
    interactions["Start"] = pd.to_datetime(interactions["Start"])
    interactions["End"] = pd.to_datetime(interactions["End"])

    # Initialize columns
    log["Participants"] = ""
    log["ID"] = 0

    # 2. Match logs to interactions (Give them an ID based on the time window)
    for int_row in interactions.itertuples():
        mask = (log["Timestamp"] >= int_row.Start) & (log["Timestamp"] <= int_row.End)
        log.loc[mask, "ID"] = int_row.ID
        log.loc[mask, "Participants"] = int_row.Count 

    # Save temporary combined file
    log.to_csv("Data.csv", index=False)

def standardize_combined_file(df):
    print("Starting robust standardization...")
    df.columns = df.columns.str.strip()

    # 1. IDENTIFY GEMINI ROWS
    # We check both Tag and Action because 'aggregate' might have shifted the text
    gemini_mask = df["Tag"].str.contains("GEMINI", na=False) | \
                  df["Action"].str.contains("GEMINI", na=False)
    
    print(f"Found {gemini_mask.sum()} Gemini rows.")

    # 2. FIX GEMINI ROWS
    if gemini_mask.any():
        # Move the user/misty dialogue from Action to Details
        df.loc[gemini_mask, "Details"] = df.loc[gemini_mask, "Action"]
        # Set standardized labels
        df.loc[gemini_mask, "Action"] = "GEMINI_IO"
        df.loc[gemini_mask, "Page"] = "/home"
        
        # Clean the Tag: Remove 'GEMINI_IO' text so only the date remains for ID filling
        df.loc[gemini_mask, "Tag"] = df.loc[gemini_mask, "Tag"].str.split(" - ").str[0]

    # 3. FILL SESSION IDs (The sess-xxxx strings)
    # This takes the ID from the navigation row above and gives it to the Gemini row below
    split_info = df["Tag"].str.split(" - ", n=1, expand=True)
    df["temp_ts"] = split_info[0]
    df["session_id"] = split_info[1]

    # ffill() propagates the last valid session ID downward
    df["session_id"] = df["session_id"].ffill().bfill()

    # 4. RECONSTRUCT TAG
    df["Tag"] = df["temp_ts"].str.strip() + " - " + df["session_id"].str.strip()

    # 5. REMOVE BUMPER PRESSES
    bumper_mask = df["Tag"].str.contains("BUMPER_PRESS", na=False) | \
                  df["Action"].str.contains("BUMPER_PRESS", na=False)
    print(f"Removing {bumper_mask.sum()} Bumper Press rows...")
    df = df[~bumper_mask]

    # Cleanup helper columns
    df = df.drop(columns=["temp_ts", "session_id"])
    return df

if __name__ == "__main__":
    try:
        # Step 1: Combine the files
        aggregate()
        
        # Step 2: Load the result for cleaning
        combined_df = pd.read_csv("Data.csv")
        
        # Step 3: Standardize (Fixes Gemini rows AND fills session IDs)
        combined_df = standardize_combined_file(combined_df)
        
        # Step 4: Remove ID = 0 
        # (CRITICAL: Do this AFTER standardization so Gemini rows have had a chance to get an ID)
        before_count = len(combined_df)
        combined_df = combined_df[combined_df["ID"] != 0]
        after_count = len(combined_df)
        
        print(f"Filtered out {before_count - after_count} rows with ID=0.")
        
        # Step 5: Final Save
        combined_df.to_csv("Data.csv", index=False)
        print("Success! Data.csv is now standardized and filtered.")
        
    except Exception as e:
        print(f"An error occurred: {e}")