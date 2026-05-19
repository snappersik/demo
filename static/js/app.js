const toastPalette = {
  success: "linear-gradient(135deg, #1f6f78, #4f8f62)",
  error: "linear-gradient(135deg, #b94743, #d9833f)",
  warning: "linear-gradient(135deg, #d9833f, #b9662b)",
  info: "linear-gradient(135deg, #4d7fa3, #1f6f78)",
};

function showToast(text, tag = "info") {
  if (!window.Toastify) return;
  Toastify({
    text,
    duration: 3600,
    gravity: "top",
    position: "right",
    close: true,
    stopOnFocus: true,
    style: { background: toastPalette[tag] || toastPalette.info },
  }).showToast();
}

function getCookie(name) {
  const parts = document.cookie ? document.cookie.split(";") : [];
  for (const part of parts) {
    const item = part.trim();
    if (item.startsWith(name + "=")) {
      return decodeURIComponent(item.slice(name.length + 1));
    }
  }
  return "";
}

const messageNode = document.getElementById("django-messages");
if (messageNode) {
  try {
    JSON.parse(messageNode.textContent).forEach((message) => showToast(message.text, message.tag));
  } catch (error) {
    console.warn("Messages parse error", error);
  }
}

document.querySelectorAll("[data-smoky-scroll]").forEach((link) => {
  link.addEventListener("click", (event) => {
    const target = document.querySelector(link.getAttribute("href"));
    if (!target) return;
    event.preventDefault();
    const overlay = document.querySelector(".smoke-overlay");
    overlay?.classList.add("is-active");
    target.scrollIntoView({ behavior: "smooth", block: "start" });
    window.setTimeout(() => overlay?.classList.remove("is-active"), 620);
  });
});

document.querySelectorAll("[data-phone-mask]").forEach((input) => {
  input.addEventListener("input", () => {
    let digits = input.value.replace(/\D/g, "");
    // Приводим все российские номера к единому формату, начинающемуся с 7
    if (digits.startsWith("8")) digits = "7" + digits.slice(1);
    if (!digits.startsWith("7")) digits = "7" + digits;
    digits = digits.slice(0, 11);
    const p = digits.padEnd(11, "_");
    input.value = `+7 (${p.slice(1, 4)}) ${p.slice(4, 7)}-${p.slice(7, 9)}-${p.slice(9, 11)}`;
  });
});

document.querySelectorAll("[data-slider]").forEach((slider) => {
  const slides = Array.from(slider.querySelectorAll("[data-slide]"));
  const dots = Array.from(slider.querySelectorAll("[data-slider-dot]"));
  const prev = slider.querySelector("[data-slider-prev]");
  const next = slider.querySelector("[data-slider-next]");
  let index = slides.findIndex((slide) => slide.classList.contains("is-active"));
  let timer = null;
  if (index < 0) index = 0;
  slider.style.setProperty("--slider-count", dots.length || slides.length);

  const showSlide = (nextIndex) => {
    slides[index]?.classList.remove("is-active");
    dots[index]?.classList.remove("is-active");
    index = (nextIndex + slides.length) % slides.length;
    slides[index]?.classList.add("is-active");
    dots[index]?.classList.add("is-active");
    window.clearInterval(timer);
    timer = window.setInterval(() => showSlide(index + 1), 3000);
  };

  prev?.addEventListener("click", () => showSlide(index - 1));
  next?.addEventListener("click", () => showSlide(index + 1));
  dots.forEach((dot, dotIndex) => dot.addEventListener("click", () => showSlide(dotIndex)));
  if (slides.length > 1) {
    timer = window.setInterval(() => showSlide(index + 1), 3000);
  }
});


const adminList = document.querySelector("[data-admin-list]");
if (adminList) {
  const controls = {
    search: document.querySelector("[data-admin-search]"),
    status: document.querySelector("[data-admin-status]"),
    type: document.querySelector("[data-admin-type]"),
    sort: document.querySelector("[data-admin-sort]"),
    empty: document.querySelector("[data-admin-empty]"),
    pagination: document.querySelector("[data-admin-pagination]"),
  };
  const rows = Array.from(adminList.querySelectorAll("[data-admin-app-row]"));
  let page = 1;
  const perPage = 8;

  const filteredRows = () => {
    const search = controls.search.value.trim().toLowerCase();
    const status = controls.status.value;
    const type = controls.type.value;
    return rows.filter((row) => {
      const searchOk = !search || row.dataset.search.toLowerCase().includes(search);
      const statusOk = !status || row.dataset.status === status;
      const typeOk = !type || row.dataset.type === type;
      return searchOk && statusOk && typeOk;
    });
  };

  const sortRows = (items) => {
    const sort = controls.sort.value;
    return items.sort((a, b) => {
      if (sort === "date") return Number(a.dataset.date) - Number(b.dataset.date);
      if (sort === "-date") return Number(b.dataset.date) - Number(a.dataset.date);
      if (sort === "status") return a.dataset.status.localeCompare(b.dataset.status, "ru");
      if (sort === "room") return a.dataset.room.localeCompare(b.dataset.room, "ru");
      return Number(b.dataset.created) - Number(a.dataset.created);
    });
  };

  const renderPagination = (totalPages) => {
    controls.pagination.innerHTML = "";
    if (totalPages <= 1) return;
    for (let i = 1; i <= totalPages; i += 1) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `btn btn-sm ${i === page ? "btn-primary" : "btn-light"}`;
      button.textContent = i;
      button.addEventListener("click", () => {
        page = i;
        applyAdminFilters(false);
      });
      controls.pagination.appendChild(button);
    }
  };

  var applyAdminFilters = (resetPage = true) => {
    if (resetPage) page = 1;
    const visibleRows = sortRows(filteredRows());
    rows.forEach((row) => row.classList.add("d-none"));
    visibleRows.forEach((row) => adminList.appendChild(row));
    const totalPages = Math.max(Math.ceil(visibleRows.length / perPage), 1);
    page = Math.min(page, totalPages);
    visibleRows.slice((page - 1) * perPage, page * perPage).forEach((row) => row.classList.remove("d-none"));
    controls.empty?.classList.toggle("d-none", visibleRows.length > 0);
    renderPagination(totalPages);
  };

  [controls.search, controls.status, controls.type, controls.sort].forEach((control) => {
    control?.addEventListener("input", () => applyAdminFilters(true));
    control?.addEventListener("change", () => applyAdminFilters(true));
  });
  applyAdminFilters(true);
}

document.querySelectorAll(".status-select").forEach((select) => {
  select.addEventListener("change", async (event) => {
    const row = event.target.closest("[data-admin-app-row]");
    const applicationId = row?.dataset.applicationId || row?.getAttribute("data-application-id");
    if (!applicationId) return;

    event.target.disabled = true;
    const formData = new FormData();
    formData.append("status", event.target.value);

    try {
      const response = await fetch(`/admin-panel/applications/${applicationId}/status/`, {
        method: "POST",
        headers: { "X-CSRFToken": getCookie("csrftoken") },
        body: formData,
      });
      const data = await response.json();
      if (!response.ok || !data.ok) throw new Error(data.error || "Не удалось изменить статус");
      row.dataset.status = data.status;
      event.target.classList.remove("badge-new", "badge-scheduled", "badge-completed");
      event.target.classList.add(data.badge_class);
      if (typeof applyAdminFilters === "function") applyAdminFilters(false);
      showToast("Статус заявки обновлен", "success");
    } catch (error) {
      showToast(error.message, "error");
    } finally {
      event.target.disabled = false;
    }
  });
});
