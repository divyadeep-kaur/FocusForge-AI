document.querySelectorAll("input[data-task-id]").forEach((checkbox) => {
  checkbox.addEventListener("change", async () => {
    const row = checkbox.closest(".task-row, .task-item");
    row?.classList.add("saving");
    const response = await fetch(`/task/${checkbox.dataset.taskId}/complete`, { method: "POST" });
    if (!response.ok) {
      checkbox.checked = !checkbox.checked;
      row?.classList.remove("saving");
      return;
    }
    const data = await response.json();
    row?.classList.toggle("complete", checkbox.checked);
    row?.classList.remove("saving");
    document.querySelectorAll(".metric-card").forEach((card) => {
      if (card.textContent.trim().startsWith("XP")) {
        card.querySelector("strong").textContent = data.xp;
        card.querySelector("small").textContent = `${data.level} level`;
      }
    });
  });
});
