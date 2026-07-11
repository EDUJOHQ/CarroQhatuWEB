const form = document.getElementById("tasacionForm");
const resultado = document.getElementById("resultado");

if (form && resultado) {
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const formData = new FormData(form);
    const data = Object.fromEntries(formData);

    const response = await fetch("/cotizar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });

    const res = await response.json();

    resultado.classList.remove("hidden");
    resultado.innerHTML = `
      <strong>Precio estimado:</strong><br>
      S/ ${res.min.toLocaleString()} – S/ ${res.max.toLocaleString()}
      <p style="font-size:12px;color:#555;">
        Estimación referencial basada en los datos ingresados.
      </p>
    `;
  });
}

