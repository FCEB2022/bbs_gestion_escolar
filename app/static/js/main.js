// main.js
document.addEventListener('DOMContentLoaded', function () {
  // Asegurar que los triggers de modal no sean botones de submit (evita parpadeo/cierre involuntario)
  // Esto convierte cualquier <button data-bs-toggle="modal"> en type="button" de forma segura.
  document.querySelectorAll('[data-bs-toggle="modal"]').forEach(el => {
    if (el.tagName === 'BUTTON') {
      // solo sobreescribimos si no está explicitado o es distinto a "button"
      if (!el.hasAttribute('type') || el.getAttribute('type').toLowerCase() !== 'button') {
        el.setAttribute('type', 'button');
      }
    }
  });

  // Botón submit -> loading
  const forms = document.querySelectorAll('form');
  forms.forEach(form => {
    form.addEventListener('submit', function () {
      const btn = this.querySelector('button[type="submit"]');
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Procesando...';
      }
    });
  });

  // Hover suave para module-card
  document.querySelectorAll('.module-card').forEach(card => {
    card.addEventListener('mouseenter', () => {
      card.style.transform = 'translateY(-8px) scale(1.02)';
    });
    card.addEventListener('mouseleave', () => {
      card.style.transform = 'translateY(0) scale(1)';
    });
  });

  // Tooltips Bootstrap
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.forEach(el => new bootstrap.Tooltip(el));

  // Lazy-load de imágenes data-src (opcional)
  if ('IntersectionObserver' in window) {
    const lazyImages = document.querySelectorAll('img[data-src]');
    const obs = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          img.src = img.dataset.src;
          img.classList.add('loaded');
          obs.unobserve(img);
        }
      });
    });
    lazyImages.forEach(img => obs.observe(img));
  }
});

document.addEventListener("DOMContentLoaded", () => {
  // Desaparece automáticamente los mensajes flash
  const alerts = document.querySelectorAll(".alert");
  alerts.forEach((alert) => {
    setTimeout(() => {
      alert.classList.remove("show");
    }, 4000);
  });
});

document.addEventListener("DOMContentLoaded", () => {
  // Efecto de hover suave en las tarjetas
  document.querySelectorAll(".module-card, .stat-card").forEach(card => {
    card.addEventListener('mouseenter', () => {
      card.style.transition = "transform 0.25s ease, box-shadow 0.25s ease";
    });
  });

  // Cierre automático de alertas flash
  const alerts = document.querySelectorAll(".alert");
  alerts.forEach(a => {
    setTimeout(() => {
      a.classList.remove("show");
    }, 4000);
  });
});