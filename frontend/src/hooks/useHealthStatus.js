import { useEffect, useState } from "react";
import { fetchHealth } from "../services/api.js";

export default function useHealthStatus() {
  const [health, setHealth] = useState({
    status: "checking",
    error: null,
  });

  useEffect(() => {
    const controller = new AbortController();

    fetchHealth(controller.signal)
      .then((result) => setHealth({ status: result.status, error: null }))
      .catch((error) => {
        if (error.name !== "AbortError") {
          setHealth({ status: "unavailable", error: error.message });
        }
      });

    return () => controller.abort();
  }, []);

  return health;
}
