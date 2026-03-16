import Lab3App from "./lab3/Lab3App.jsx";
import Lab4App from "./lab4/Lab4App.jsx";
import "./App.css";

function detectLab() {
  const hostname = window.location.hostname.toLowerCase();
  const params = new URLSearchParams(window.location.search);
  const forcedLab = params.get("lab");

  if (forcedLab === "4") {
    return "lab4";
  }
  if (forcedLab === "3") {
    return "lab3";
  }
  if (hostname.startsWith("lab4.")) {
    return "lab4";
  }
  if (hostname.startsWith("lab3.")) {
    return "lab3";
  }
  if (window.location.pathname.startsWith("/lab4")) {
    return "lab4";
  }
  return "lab3";
}

function App() {
  return detectLab() === "lab4" ? <Lab4App /> : <Lab3App />;
}

export default App;
