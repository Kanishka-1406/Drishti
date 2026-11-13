import {
  useEffect,
  useRef,
  useState,
} from "react";
import api from "../services/api";


const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const WS_URL = `${API_BASE.replace(/^http/, "ws")}/ws/sensors`;


export default function useSensorWebSocket(
  nodeId
) {
  const [reading, setReading] =
    useState(null);

  const [
    sourceMode,
    setSourceMode,
  ] = useState(null);

  const [
    connectionStatus,
    setConnectionStatus,
  ] = useState("connecting");

  const socketRef = useRef(null);

  const retryRef = useRef(null);
  const [anomaly, setAnomaly] = useState(null);
  const [history, setHistory] = useState([]);


  useEffect(() => {
    let cancelled = false;

    async function loadLatest() {
      if (!nodeId) return;
      try {
        const { data } = await api.get(`/sensors/${nodeId}/latest`);
        if (!cancelled && data.reading) {
          setReading(data.reading);
          setHistory([{ ...data.reading, anomaly_state: "RECORDED" }]);
          setSourceMode(data.source_mode || "RECORDED");
        }
      } catch {
        if (!cancelled) setSourceMode(null);
      }
    }


    function connect() {
      if (cancelled) {
        return;
      }

      setConnectionStatus(
        "connecting"
      );

      const socket =
        new WebSocket(
          WS_URL
        );

      socketRef.current =
        socket;


      socket.onopen = () => {
        if (cancelled) {
          socket.close();
          return;
        }

        setConnectionStatus(
          "connected"
        );
      };


      socket.onmessage = (
        event
      ) => {
        try {
          const message =
            JSON.parse(
              event.data
            );

          if (
            message.type !==
            "sensor_reading"
          ) {
            return;
          }

          if (
            nodeId &&
            message.node_id !==
              nodeId
          ) {
            return;
          }

          setReading(message.reading);
          setHistory((items) => [...items.slice(-11), { ...message.reading, anomaly_state: message.anomaly?.state }]);

          setAnomaly(
            message.anomaly ?? null
          );

          setSourceMode(
            message.source_mode
          );
        } catch (error) {
          console.error(
            "Invalid WebSocket message",
            error
          );
        }
      };


      socket.onerror = () => {
        setConnectionStatus(
          "error"
        );
      };


      socket.onclose = () => {
        if (cancelled) {
          return;
        }

        setConnectionStatus(
          "disconnected"
        );

        retryRef.current =
          setTimeout(
            connect,
            2000
          );
      };
    }


    loadLatest();
    connect();


    return () => {
      cancelled = true;

      if (retryRef.current) {
        clearTimeout(
          retryRef.current
        );
      }

      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [nodeId]);


  return {
    reading,
    anomaly,
    sourceMode,
    connectionStatus,
    history,
  };
}
