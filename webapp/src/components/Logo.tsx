import { cn } from "@/lib/utils";
import React from "react";

type Props = { className?: string };

const Logo = ({ className }: Props) => {
  return (
    <h1 className={cn("text-2xl font-bold text-white", className)}>Synapse</h1>
  );
};

export default Logo;
