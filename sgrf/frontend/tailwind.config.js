/**
 * Identidad visual definida en el Capitulo 6.4 de la especificacion:
 * azul francia como color principal, blanco como secundario, y verde,
 * amarillo y rojo reservados para los estados.
 *
 * Los nombres estan en el Lenguaje Ubicuo del proyecto para que una clase
 * de Tailwind se lea igual que la especificacion.
 */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        azul: {
          DEFAULT: "#0B5FA5",
          oscuro: "#073F6E",
          medio: "#2A7FC4",
          claro: "#E8F1F9",
        },
        tinta: {
          DEFAULT: "#1A2733",
          suave: "#5A6875",
          tenue: "#8B97A3",
        },
        exito: "#15803D",
        advertencia: "#B45309",
        error: "#B91C1C",
        papel: "#FAFBFC",
        borde: "#DDE4EB",
      },
      fontFamily: {
        /* Capitulo 6.4: tipografia sans serif. */
        sans: [
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "sans-serif",
        ],
      },
      fontSize: {
        /* Base de 16 px segun el Capitulo 6.4. Las cantidades de los
           ingredientes usan un escalon mayor porque se leen cocinando. */
        base: ["1rem", { lineHeight: "1.6" }],
        cantidad: ["1.375rem", { lineHeight: "1.3", fontWeight: "600" }],
      },
      borderRadius: {
        pieza: "0.625rem",
      },
      boxShadow: {
        tarjeta: "0 1px 2px rgba(26, 39, 51, 0.06), 0 4px 12px rgba(26, 39, 51, 0.05)",
        elevada: "0 2px 4px rgba(26, 39, 51, 0.08), 0 12px 28px rgba(26, 39, 51, 0.10)",
      },
    },
  },
  plugins: [],
};
