document$.subscribe(() => {
  const url = encodeURIComponent(window.location.href);

  const style = document.createElement("style");
  style.textContent = `
    .md-social-share {
      margin-top: 2rem;
      display: flex;
      justify-content: flex-end;
    }

    .md-social-share a {
      font-size: 1.3rem;
      color: var(--md-default-fg-color--lighter);
      transition: color 0.2s ease, transform 0.2s ease;
    }

    .md-social-share svg {
      width: 1.2em;
      height: 1.2em;
      fill: currentColor;
    }
  `;
  document.head.appendChild(style);

  const html = `
    <div class="md-social-share">
      <a href="https://t.me/share/url?url=${url}" title="Telegram" target="_blank" rel="noopener">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240">
          <path d="M120 0C53.7 0 0 53.7 0 120s53.7 120 120 120 120-53.7 120-120S186.3 0 120 0zm58.2 80.6-17.6 82.6c-1.3 5.8-4.7 7.2-9.5 4.5l-26.3-19.4-12.7 12.3c-1.4 1.4-2.6 2.6-5.2 2.6l1.9-26.9 49-44.3c2.1-1.9-.4-3-3.2-1.1l-60.6 38.2-26.2-8.2c-5.7-1.8-5.8-5.7 1.2-8.4l102.5-39.5c4.8-1.8 9 1.1 7.5 8.1z"/>
        </svg>
      </a>
    </div>
  `;

  const container = document.createElement("div");
  container.innerHTML = html;

  const target = document.querySelector(".md-content__inner");
  if (target) target.appendChild(container);
});
