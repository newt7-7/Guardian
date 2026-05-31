document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.querySelector('.nav-toggle');
  const navLinks = document.querySelector('.nav-links');

  if (toggle) {
    toggle.addEventListener('click', () => {
      toggle.classList.toggle('open');
      navLinks.classList.toggle('open');
    });
  }

  document.addEventListener('click', (e) => {
    if (toggle && navLinks && !toggle.contains(e.target) && !navLinks.contains(e.target)) {
      toggle.classList.remove('open');
      navLinks.classList.remove('open');
    }
  });

  const filterBtns = document.querySelectorAll('.filter-btn');
  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const parent = btn.closest('.filter-bar') || btn.parentElement;
      parent.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });

  const currentPage = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-links a').forEach(link => {
    const href = link.getAttribute('href');
    if (href === currentPage) {
      link.classList.add('active');
    }
  });

  const contactForm = document.querySelector('.login-form');
  if (contactForm) {
    contactForm.addEventListener('submit', (e) => {
      e.preventDefault();
      alert('Thank you! This is a demo interface. In production, this would connect to a secure authentication system.');
    });
  }

  const newsletterForms = document.querySelectorAll('.newsletter-form');
  newsletterForms.forEach(form => {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const input = form.querySelector('input[type="email"]');
      if (input && input.value) {
        alert('Thank you for subscribing! You will receive our latest updates.');
        input.value = '';
      }
    });
  });

  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const href = this.getAttribute('href');
      if (href === '#' || !href) return;
      e.preventDefault();
      const target = document.querySelector(href);
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  document.querySelectorAll('.portal-card a[href="#"]').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const text = link.textContent.trim();
      if (text.includes('Browse')) {
        alert('Resource library access requires authentication. This demo would redirect to a secure login page.');
      } else if (text.includes('Report')) {
        alert('Incident reporting requires an active account. This demo would connect to our 24/7 response system.');
      } else if (text.includes('Forgot')) {
        alert('Password reset functionality would send a secure reset link to your registered email address.');
      } else if (text.includes('Request Access')) {
        alert('Account registration requires verification. This demo would redirect to a secure registration form.');
      }
    });
  });
});
