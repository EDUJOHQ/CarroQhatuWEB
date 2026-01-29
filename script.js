const form = document.getElementById("tasacionForm");
const resultado = document.getElementById("resultado");

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const formData = new FormData(form);
  const data = Object.fromEntries(formData);

  const response = await fetch("http://127.0.0.1:5000/tasar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });

  const res = await response.json();

  resultado.classList.remove("hidden");
  resultado.innerHTML = `
    <strong>Precio estimado:</strong><br>
    S/ ${res.precio_min.toLocaleString()} – S/ ${res.precio_max.toLocaleString()}
    <p style="font-size:12px;color:#555;">
      Estimación referencial basada en los datos ingresados.
    </p>
  `;
});