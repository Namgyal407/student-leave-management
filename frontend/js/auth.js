"use strict";

// Login endpoint from backend/routes/auth.py. No backend changes required.
const API_BASE_URL = "http://localhost:5000";
const AUTH_STORAGE_KEY = "slm_auth";

const loginForm = document.getElementById("loginForm");
const loginView = document.getElementById("loginView");
const successView = document.getElementById("successView");
const emailInput = document.getElementById("email");
const passwordInput = document.getElementById("password");
const rememberMe = document.getElementById("rememberMe");
const formMessage = document.getElementById("formMessage");
const emailError = document.getElementById("emailError");
const passwordError = document.getElementById("passwordError");
const togglePassword = document.getElementById("togglePassword");
const submitButton = document.getElementById("submitButton");
const buttonText = document.getElementById("buttonText");
const buttonSpinner = document.getElementById("buttonSpinner");
const buttonArrow = document.getElementById("buttonArrow");

function showMessage(message) {
  formMessage.textContent = message;
  formMessage.hidden = false;
}

function clearMessage() {
  formMessage.textContent = "";
  formMessage.hidden = true;
}

function setFieldError(input, errorElement, message) {
  input.setAttribute("aria-invalid", String(Boolean(message)));
  errorElement.textContent = message;
  errorElement.hidden = !message;
}

function isEmail(email) {
  // Basic client-side validation; the server performs the actual authentication.
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function setLoading(loading) {
  submitButton.disabled = loading;
  buttonText.textContent = loading ? "Signing in…" : "Sign in";
  buttonSpinner.hidden = !loading;
  buttonArrow.hidden = loading;
  emailInput.readOnly = loading;
  passwordInput.readOnly = loading;
}

async function apiRequest(path, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 12000);

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      signal: controller.signal,
      headers: { Accept: "application/json", ...(options.headers || {}) },
    });
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      const error = new Error(typeof data.error === "string" ? data.error : `Request failed (${response.status}).`);
      error.status = response.status;
      throw error;
    }
    return data;
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("The request timed out. Please try again.");
    }
    if (error instanceof TypeError) {
      throw new Error("Cannot connect to the server. Check that the Flask backend is running on port 5000.");
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

function saveAuth(token, user, persistent) {
  const target = persistent ? localStorage : sessionStorage;
  const other = persistent ? sessionStorage : localStorage;
  other.removeItem(AUTH_STORAGE_KEY);
  target.setItem(AUTH_STORAGE_KEY, JSON.stringify({ token, user }));
}

function storedAuth() {
  for (const storage of [sessionStorage, localStorage]) {
    try {
      const value = storage.getItem(AUTH_STORAGE_KEY);
      if (!value) continue;
      const parsed = JSON.parse(value);
      if (typeof parsed.token === "string" && parsed.token) return { ...parsed, storage };
    } catch (_error) {
      storage.removeItem(AUTH_STORAGE_KEY);
    }
  }
  return null;
}

function clearAuth() {
  sessionStorage.removeItem(AUTH_STORAGE_KEY);
  localStorage.removeItem(AUTH_STORAGE_KEY);
}

function initials(name) {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  return (parts.length > 1 ? `${parts[0][0]}${parts[parts.length - 1][0]}` : (parts[0] || "U").slice(0, 2)).toUpperCase();
}

function showSignedIn(user) {
  const name = user.name || "User";
  const role = user.role || "member";
  const roleLabels = { student: "Student", faculty: "Faculty", admin: "Administrator" };

  document.getElementById("welcomeText").textContent = `Welcome back, ${name.split(/\s+/)[0]}!`;
  document.getElementById("accountName").textContent = name;
  document.getElementById("accountEmail").textContent = user.email || emailInput.value.trim();
  document.getElementById("accountRole").textContent = roleLabels[role] || role;
  document.getElementById("accountAvatar").textContent = initials(name);
  loginView.hidden = true;
  successView.hidden = false;
  passwordInput.value = "";
  document.getElementById("welcomeText").focus();
}

function showSignIn() {
  successView.hidden = true;
  loginView.hidden = false;
  clearMessage();
  passwordInput.value = "";
  emailInput.focus();
}

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (submitButton.disabled) return;

  clearMessage();
  const email = emailInput.value.trim();
  const password = passwordInput.value;
  setFieldError(emailInput, emailError, "");
  setFieldError(passwordInput, passwordError, "");

  let valid = true;
  if (!email || !isEmail(email)) {
    setFieldError(emailInput, emailError, "Enter a valid email address.");
    valid = false;
  }
  if (!password) {
    setFieldError(passwordInput, passwordError, "Enter your password.");
    valid = false;
  }
  if (!valid) {
    (emailInput.getAttribute("aria-invalid") === "true" ? emailInput : passwordInput).focus();
    return;
  }

  setLoading(true);
  try {
    const data = await apiRequest("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    // Actual repository: { token, user: { name, role, email } }
    // Also supports task handout: { token, name, role }
    const user = data.user && typeof data.user === "object" ? data.user : {
      name: data.name,
      role: data.role,
      email,
    };
    if (!data.token || typeof data.token !== "string" || !user.role) {
      throw new Error("The server returned an unexpected login response.");
    }

    saveAuth(data.token, user, rememberMe.checked);
    showSignedIn(user);
  } catch (error) {
    showMessage(error.message || "Unable to sign in. Please try again.");
  } finally {
    setLoading(false);
  }
});

emailInput.addEventListener("input", () => {
  setFieldError(emailInput, emailError, "");
  clearMessage();
});
passwordInput.addEventListener("input", () => {
  setFieldError(passwordInput, passwordError, "");
  clearMessage();
});

togglePassword.addEventListener("click", () => {
  const visible = passwordInput.type === "password";
  passwordInput.type = visible ? "text" : "password";
  togglePassword.setAttribute("aria-pressed", String(visible));
  togglePassword.setAttribute("aria-label", visible ? "Hide password" : "Show password");
  document.getElementById("eyeOpen").hidden = visible;
  document.getElementById("eyeClosed").hidden = !visible;
  passwordInput.focus();
});

document.getElementById("signOutButton").addEventListener("click", () => {
  clearAuth();
  showSignIn();
});

// Check a saved token before treating a previous session as signed in.
(async function restoreSession() {
  const saved = storedAuth();
  if (!saved) return;
  rememberMe.checked = saved.storage === localStorage;

  try {
    const data = await apiRequest("/api/me", {
      headers: { Authorization: `Bearer ${saved.token}` },
    });
    if (data.user && !loginForm.matches(":focus-within")) {
      showSignedIn(data.user);
    }
  } catch (error) {
    // Expired/invalid tokens should never restore a session.
    if (error.status === 401 || error.status === 403) clearAuth();
  }
})();
