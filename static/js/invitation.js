const observer = new IntersectionObserver(
  (entries) => entries.forEach((entry) => {
    if (entry.isIntersecting) entry.target.classList.add("in-view");
  }),
  { threshold: 0.15 }
);

document.querySelectorAll(".reveal").forEach((el) => observer.observe(el));

const invite = document.querySelector(".wedding-invite");
const countdown = document.getElementById("countdown");

function pad(value) {
  return String(value).padStart(2, "0");
}

function updateCountdown() {
  if (!invite || !countdown) return;
  const target = new Date(invite.dataset.eventDate);
  const now = new Date();
  const diff = Math.max(target.getTime() - now.getTime(), 0);
  const totalSeconds = Math.floor(diff / 1000);

  const days = Math.floor(totalSeconds / 86400);
  const hours = Math.floor((totalSeconds % 86400) / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  countdown.querySelector("[data-days]").textContent = pad(days);
  countdown.querySelector("[data-hours]").textContent = pad(hours);
  countdown.querySelector("[data-minutes]").textContent = pad(minutes);
  countdown.querySelector("[data-seconds]").textContent = pad(seconds);
}

updateCountdown();
setInterval(updateCountdown, 1000);

document.querySelectorAll("[data-copy]").forEach((button) => {
  button.addEventListener("click", async () => {
    await navigator.clipboard.writeText(button.dataset.copy);
    const original = button.textContent;
    button.textContent = "Enlace copiado";
    setTimeout(() => (button.textContent = original), 1600);
  });
});

const music = document.getElementById("weddingMusic");
const musicButton = document.getElementById("musicButton");

if (music && musicButton) {
  musicButton.addEventListener("click", async () => {
    if (music.paused) {
      await music.play();
      musicButton.textContent = "Ⅱ";
    } else {
      music.pause();
      musicButton.textContent = "♪";
    }
  });
}
