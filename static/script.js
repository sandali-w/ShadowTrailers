async function api(route, method = "GET", data = null) {
  const options = { method: method, headers: { "Content-Type": "application/json" } };
  if (data) options.body = JSON.stringify(data);
  try {
    const res = await fetch(route, options);
    return { ok: res.ok, data: await res.json() };
  } catch (err) {
    return { ok: false, data: { error: "Cannot reach the server" } };
  }
}

document.getElementById("signin-btn").addEventListener("click", async () => {
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;
  const res = await api("/api/login", "POST", { username, password });
  document.getElementById("message").textContent =
    res.ok ? "Welcome, " + res.data.username + "!" : res.data.error;
});
