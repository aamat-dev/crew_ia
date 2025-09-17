import { Status } from "@/ui/theme";

export interface RunAgent {
  id: string;
  name: string;
  role: "Superviseur" | "Manager" | "Exécutant";
}

export interface RunEvent {
  timestamp: string;
  message: string;
}

export interface Run {
  id: string;
  title: string;
  status: Status;
  date: string;
  duration: string;
  agents: RunAgent[];
  throughput: number;
  successRate: number;
  errors?: string[];
  logs: RunEvent[];
  description?: string;
}
