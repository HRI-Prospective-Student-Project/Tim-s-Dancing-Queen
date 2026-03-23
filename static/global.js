/**
 * F&M Social Robotics Lab - Global Controller
 * Optimized for Research Logging & Session Persistence
 */

// 1. SESSION ID LOGIC
let sessionId = localStorage.getItem('robot_session_id');

if (window.location.pathname === "/" || !sessionId) {
    sessionId = "sess-" + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('robot_session_id', sessionId);
}
const CURRENT_SESSION = sessionId;

// 2. INACTIVITY TIMER
let idleTimer;
const FIVE_MINUTES = 5 * 60 * 1000; 

function resetIdleTimer() {
    clearTimeout(idleTimer);
    idleTimer = setTimeout(() => {
        logInteraction("SESSION_TIMEOUT", "Resetting due to inactivity");
        localStorage.removeItem('robot_session_id');
        window.location.href = "/";
    }, FIVE_MINUTES);
}

window.onload = resetIdleTimer;
document.onmousedown = resetIdleTimer; 
document.onkeydown = resetIdleTimer;

/**
 * 3. THE COMPREHENSIVE LOGGER
 * Standardized Fetch for all research events.
 */
async function logInteraction(event, details) {
    try {
        await fetch('/log_event', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sessionId: CURRENT_SESSION,
                event: event,
                details: details,
                page: window.location.pathname
            })
        });
    } catch (err) {
        console.warn("Log failed", err);
    }
}

/**
 * 4. ROBOT CONTROLS
 */
function speakText(text) {
    logInteraction("ROBOT_SPEECH_START", text.substring(0, 60) + "...");
    fetch("/speak", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text })
    });
}

function stopSpeech() {
    logInteraction("ROBOT_STOP", "Interrupt triggered");
    fetch("/stop", { method: "POST", headers: { "Content-Type": "application/json" } });
}

function handleNav(destination) {
    logInteraction("NAV_CLICK", `To: ${destination}`);
    stopSpeech(); 
}

/**
 * 5. AUTOMATIC EVENT LISTENERS
 */

// Fix for the 415 error: Force Beacon to use JSON blob
window.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') {
        const data = JSON.stringify({
            sessionId: CURRENT_SESSION,
            event: "PAGE_EXIT",
            details: "User left page",
            page: window.location.pathname
        });
        const blob = new Blob([data], { type: 'application/json' });
        navigator.sendBeacon('/log_event', blob);
    }
});

// Auto-log all link clicks
document.addEventListener('click', (e) => {
    const link = e.target.closest('a');
    if (link && !link.onclick) { 
        logInteraction("LINK_CLICK", link.href);
    }
});

// Error tracking
window.onerror = function(msg, url, line) {
    logInteraction("JS_ERROR", `${msg} @ line ${line}`);
};