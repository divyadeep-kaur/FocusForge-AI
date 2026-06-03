document.querySelectorAll(".timer").forEach((timer) => {
  const display = timer.querySelector(".timer-display");
  const progress = timer.querySelector(".timer-progress");
  const startBtn = timer.querySelector(".start-timer");
  const pauseBtn = timer.querySelector(".pause-timer");
  const resetBtn = timer.querySelector(".reset-timer");
  const customInput = timer.querySelector(".custom-time input");
  const customBtn = timer.querySelector(".apply-custom");
  const tabs = timer.querySelectorAll(".mode-tabs button");
  const circumference = 2 * Math.PI * 54;
  let total = Number(timer.dataset.duration || 1500);
  let remaining = total;
  let interval = null;

  progress.style.strokeDasharray = circumference;

  function draw() {
    const minutes = Math.floor(remaining / 60).toString().padStart(2, "0");
    const seconds = Math.floor(remaining % 60).toString().padStart(2, "0");
    display.textContent = `${minutes}:${seconds}`;
    progress.style.strokeDashoffset = circumference * (1 - remaining / total);
  }

  function setDuration(minutes) {
    total = Math.max(60, Number(minutes) * 60);
    remaining = total;
    clearInterval(interval);
    interval = null;
    startBtn.textContent = "Start";
    draw();
  }

  function tick() {
    if (remaining <= 0) {
      clearInterval(interval);
      interval = null;
      timer.classList.add("finished");
      startBtn.textContent = "Start";
      return;
    }
    remaining -= 1;
    draw();
  }

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((item) => item.classList.remove("active"));
      tab.classList.add("active");
      setDuration(tab.dataset.minutes);
      customInput.value = tab.dataset.minutes;
    });
  });

  customBtn.addEventListener("click", () => setDuration(customInput.value));
  startBtn.addEventListener("click", () => {
    if (!interval) {
      timer.classList.remove("finished");
      interval = setInterval(tick, 1000);
      startBtn.textContent = "Running";
    }
  });
  pauseBtn.addEventListener("click", () => {
    clearInterval(interval);
    interval = null;
    startBtn.textContent = "Resume";
  });
  resetBtn.addEventListener("click", () => setDuration(total / 60));
  draw();
});

const modal = document.getElementById("focusModal");
const openModal = document.getElementById("openFocusModal");
if (modal && openModal) {
  openModal.addEventListener("click", () => modal.classList.add("show"));
  modal.querySelector(".close-modal").addEventListener("click", () => modal.classList.remove("show"));
  modal.addEventListener("click", (event) => {
    if (event.target === modal) modal.classList.remove("show");
  });
}
