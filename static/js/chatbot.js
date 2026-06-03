const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const chatStream = document.getElementById("chatStream");

function addMessage(type, author, text) {
  const node = document.createElement("div");
  node.className = `chat-message ${type}`;
  node.innerHTML = `<strong></strong><p></p>`;
  node.querySelector("strong").textContent = author;
  node.querySelector("p").textContent = text;
  chatStream.appendChild(node);
  chatStream.scrollTop = chatStream.scrollHeight;
}

chatForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = chatInput.value.trim();
  if (!text) return;
  addMessage("user", "You", text);
  chatInput.value = "";
  const response = await fetch("/api/coach", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text }),
  });
  const data = await response.json();
  addMessage("bot", "FocusForge Coach", data.reply);
});
