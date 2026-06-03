document.querySelectorAll(".reward-card.unlocked").forEach((card, index) => {
  card.style.animationDelay = `${index * 80}ms`;
});
