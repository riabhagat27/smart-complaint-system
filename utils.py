def categorize_complaint(text: str):
    text = text.lower()

    if any(word in text for word in ["Current","Voltage","Resistance","Power","Energy","Charge","Circuit","Conductor","Insulator","Semiconductor","Resistor","Capacitor","Inductor","Diode","Transistor","Switch","Fuse","Relay","Battery","Cell","AC","DC","Single-phase","Three-phase","Short circuit","Overload","Earthing","Grounding","Neutral wire","Live wire","Distribution board","Circuit breaker","MCB","Ammeter","Voltmeter","Ohmmeter","Multimeter","Wattmeter","Earth fault","Insulation failure","Shock hazard","Overheating"]):
        return "Electrical"

    elif any(word in text for word in ["wifi", "internet", "network", "lan"]):
        return "Network"

    elif any(word in text for word in ["Plumbing","Pipe","Pipeline","Water supply","Drainage","Sewer","Tap","Faucet","Valve","Leak","Clog","Blockage","Overflow","Sink","Toilet","Flush","Tank","Water tank","Pump","Motor","Gasket","Seal","Joint","Fitting","Elbow","Coupling","Tee","Wrench","Plunger","Drain cleaner","Pipe wrench","Water pressure","Backflow","Hot water","Cold water","Waste water","Sanitation","Leakage","Repair","Maintenance","Installation","Inspection","Pipe burst","Crack","Corrosion"]):
        return "Plumbing"

    elif any(word in text for word in ["Cleaning","Sanitization","Disinfection","Hygiene","Dusting","Sweeping","Mopping","Vacuuming","Scrubbing","Wiping","Polishing","Rinsing","Detergent","Soap","Cleaner","Disinfectant","Sanitizer","Broom","Mop","Bucket","Cloth","Sponge","Brush","Dustbin","Garbage","Waste","Trash","Recycle","Odor","Stain","Grease","Spill","Litter","Cleanliness","Maintenance","Housekeeping","Deep cleaning","Surface cleaning","Waste disposal","Sanitary","Sterilization","Hygienic","Deodorizer","Cleaning agent","Tools"]):
        return "Cleaning"

    else:
        return "General"


def detect_priority(text: str):
    text = text.lower()

    if any(word in text for word in ["urgent", "emergency", "leak", "fire", "broken"]):
        return "High"

    elif any(word in text for word in ["soon", "issue", "problem"]):
        return "Medium"

    return "Low"