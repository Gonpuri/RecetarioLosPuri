/**
 * Identidad visual definida en el Capitulo 6.4 de la especificacion:
 * azul francia como color principal, blanco como secundario, y verde,
 * amarillo y rojo reservados para los estados.
 *
 * El azul se mantiene como color de accion (botones, enlaces, foco): eso
 * es lo que la especificacion fija como "principal". A su alrededor, la
 * paleta se reconstruyo calida -fondos color hueso, tinta con base marron
 * en lugar de azulada, sombras tibias- para que la aplicacion se sienta
 * como un recetario de cocina y no como un panel administrativo.
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
          claro: "#EAF1F8",
        },
        /* Acento calido: terracota. Decorativo -chips, detalles, hover
           suaves- y nunca para estados, que siguen siendo exito/advertencia/
           error segun el Capitulo 6.4. */
        calido: {
          DEFAULT: "#C1622D",
          oscuro: "#9A4A1E",
          claro: "#F5E4D7",
        },
        tinta: {
          DEFAULT: "#2B241E",
          suave: "#6B5D50",
          tenue: "#9C8F80",
        },
        exito: "#166534",
        advertencia: "#B45309",
        error: "#B42318",
        papel: "#FBF7F0",
        borde: "#E7DDD0",
      },
      fontFamily: {
        /* Capitulo 6.4: tipografia sans serif para el texto de la
           aplicacion. Los titulos usan ademas una serif calida (Fraunces)
           como acento editorial, al estilo de un libro de cocina -no
           reemplaza la sans del cuerpo, la complementa. */
        sans: [
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "sans-serif",
        ],
        titulo: ["Fraunces", "Georgia", "serif"],
      },
      fontSize: {
        /* Base de 16 px segun el Capitulo 6.4. Las cantidades de los
           ingredientes usan un escalon mayor porque se leen cocinando. */
        base: ["1rem", { lineHeight: "1.6" }],
        cantidad: ["1.375rem", { lineHeight: "1.3", fontWeight: "600" }],
      },
      borderRadius: {
        pieza: "0.75rem",
        generosa: "1.25rem",
      },
      boxShadow: {
        tarjeta: "0 1px 2px rgba(60, 42, 24, 0.07), 0 4px 14px rgba(60, 42, 24, 0.06)",
        elevada: "0 3px 6px rgba(60, 42, 24, 0.09), 0 14px 32px rgba(60, 42, 24, 0.12)",
      },
    },
  },
  plugins: [],
};
