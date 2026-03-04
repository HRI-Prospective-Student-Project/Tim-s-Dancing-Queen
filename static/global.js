/**
 * F&M Social Robotics Lab - Global Controller
 * Comprehensive Logging, Speech, and Session Lifecycle Management
 */

// 1. SESSION INITIALIZATION
const sessionStartTime = Date.now();
console.log("[SYSTEM]: Global Logging Active. Session started at " + new Date().toISOString());

/**
 * 2. THE COMPREHENSIVE LOGGER
 * Sends interaction data to the Flask backend /log_event route.
 * @param {string} event - The category of action (e.g., 'NAV_CLICK', 'FAQ_CLICK')
 * @param {string} details - Specific data (e.g., 'Why F&M CS')
 */
function logInteraction(event, details) {
    const payload = {
        timestamp: new Date().toISOString(),
        event: event,
        details: details,
        page: window.location.pathname,
        viewport: `${window.innerWidth}x${window.innerHeight}`
    };

    console.log(`[LOG]: ${event} | ${details}`);

    fetch('/log_event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    }).catch(err => {
        // Fallback for when the server is unreachable during development
        console.warn("Logging failed. Flask server might be offline.", err);
    });
}

/**
 * 3. CENTRALIZED SPEECH CONTROLS
 * Handles sending text to Misty and logging the start/stop of speech.
 */
function speakText(text) {
    // Log the intent to speak (useful for HRI interaction analysis)
    logInteraction("ROBOT_SPEECH_START", text.substring(0, 60) + (text.length > 60 ? "..." : ""));
    
    fetch("/speak", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text })
    }).catch(err => {
        logInteraction("ERROR", "Speech server (Flask) unreachable");
        console.error("Speech request failed:", err);
    });
}

function stopSpeech() {
    // Track if the user manually silenced the robot or "barged in" by navigating
    logInteraction("ROBOT_SPEECH_STOP", "User requested silence or interrupted flow");
    
    // sendBeacon is used for reliability if this is called during page exit
    navigator.sendBeacon("/stop");
}

/**
 * 4. NAVIGATION WRAPPER
 * Standardizes how links are handled to ensure logs are captured before the page changes.
 */
function handleNav(destination) {
    logInteraction("NAV_CLICK", `Destination: ${destination}`);
    stopSpeech(); // Most HRI studies prefer the robot stops talking when the screen changes
}

/**
 * 5. AUTOMATIC EVENT LISTENERS (The "Comprehensive" Logic)
 */

// A. Log Page Duration on Exit
// Uses 'beforeunload' to calculate exactly how long the user engaged with the current page.
window.addEventListener('beforeunload', () => {
    const durationSeconds = Math.round((Date.now() - sessionStartTime) / 1000);
    const exitData = JSON.stringify({
        event: "PAGE_EXIT",
        details: `Engagement Duration: ${durationSeconds}s`,
        page: window.location.pathname,
        timestamp: new Date().toISOString()
    });
    
    // sendBeacon is the browser's way of ensuring the log hits the server even as the page closes
    navigator.sendBeacon('/log_event', exitData);
});

// B. Log Tab Switching / Focus
// Detects if the user gets distracted or leaves the browser tab open in the background.
document.addEventListener('visibilitychange', () => {
    const state = document.hidden ? "BACKGROUND" : "FOREGROUND";
    logInteraction("TAB_FOCUS_CHANGE", `User moved page to ${state}`);
});

// C. Capture All Link Clicks Automatically
// A "safety net" listener that catches any links you might have forgotten to add handleNav to.
document.addEventListener('click', (e) => {
    const link = e.target.closest('a');
    if (link && !link.onclick) { // Only logs if we haven't already logged it via handleNav
        logInteraction("LINK_CLICK_AUTO", `Link: ${link.href}`);
    }
});

// D. Error Tracking
// Automatically logs any JavaScript errors that happen in the browser.
window.onerror = function(message, source, lineno, colno, error) {
    logInteraction("JS_ERROR", `${message} at ${source}:${lineno}`);
};