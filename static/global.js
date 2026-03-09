/**
 * F&M Social Robotics Lab - Global Controller
 * Comprehensive Logging, Speech, and Session Lifecycle Management
 */

// 1. SESSION ID LOGIC
// We check localStorage so the ID persists as they move between pages.
let sessionId = localStorage.getItem('robot_session_id');

// ONLY generate a new ID if we are on the Home Page (/) OR if no ID exists yet
if (window.location.pathname === "/" || !sessionId) {
    sessionId = "sess-" + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('robot_session_id', sessionId);
    console.log("[SYSTEM]: New Session ID Generated: " + sessionId);
}

// 2. INACTIVITY TIMER (5 Minutes)
let idleTimer;
const FIVE_MINUTES = 5 * 60 * 1000; 

function resetIdleTimer() {
    clearTimeout(idleTimer);
    idleTimer = setTimeout(autoReset, FIVE_MINUTES);
}

function autoReset() {
    // Log the timeout before we leave the page
    logInteraction("SESSION_TIMEOUT", "User inactive for 5 minutes. Resetting to Home.");
    
    // Redirect to home (which will trigger a new Session ID)
    window.location.href = "/";
}

// Listen for "Signs of Life" to reset the 5-minute clock
window.onload = resetIdleTimer;
document.onmousemove = resetIdleTimer;
document.onmousedown = resetIdleTimer; 
document.onkeydown = resetIdleTimer;

/**
 * 3. THE COMPREHENSIVE LOGGER
 * Sends interaction data to the Flask backend.
 */
function logInteraction(event, details) {
    const payload = {
        sessionId: localStorage.getItem('robot_session_id'), // Use the persistent ID
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
        console.warn("Logging failed. Flask server might be offline.", err);
    });
}

/**
 * 4. CENTRALIZED SPEECH & NAV CONTROLS
 */
function speakText(text) {
    logInteraction("ROBOT_SPEECH_START", text.substring(0, 60));
    
    fetch("/speak", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text })
    }).catch(err => console.error("Speech failed:", err));
}

function stopSpeech() {
    logInteraction("ROBOT_SPEECH_STOP", "User requested silence");
    navigator.sendBeacon("/stop");
}

function handleNav(destination) {
    logInteraction("NAV_CLICK", `Destination: ${destination}`);
    stopSpeech(); 
}

/**
 * 5. AUTOMATIC EVENT LISTENERS
 */

// A. Log Page Duration on Exit
window.addEventListener('beforeunload', () => {
    const exitData = JSON.stringify({
        sessionId: localStorage.getItem('robot_session_id'),
        event: "PAGE_EXIT",
        details: `User left or navigated away`,
        page: window.location.pathname,
        timestamp: new Date().toISOString()
    });
    navigator.sendBeacon('/log_event', exitData);
});

// B. Capture All Link Clicks Automatically
document.addEventListener('click', (e) => {
    const link = e.target.closest('a');
    if (link && !link.onclick) { 
        logInteraction("LINK_CLICK_AUTO", `Link: ${link.href}`);
    }
});

// C. Error Tracking
window.onerror = function(message, source, lineno) {
    logInteraction("JS_ERROR", `${message} at ${lineno}`);
};