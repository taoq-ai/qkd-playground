import { useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Text, Line } from "@react-three/drei";
import * as THREE from "three";

export interface BlochSphereProps {
  /** Bloch vector as [x, y, z] */
  readonly stateVector: readonly [number, number, number];
  /** "Z" for rectilinear basis, "X" for diagonal basis */
  readonly basis: "Z" | "X";
}

const Z_COLOR = "#4fd1c5"; // accent / rectilinear
const X_COLOR = "#c084fc"; // purple / diagonal

function SphereWireframe() {
  return (
    <>
      {/* Solid semi-transparent sphere */}
      <mesh>
        <sphereGeometry args={[1, 32, 32]} />
        <meshStandardMaterial
          color="#1a1a1a"
          transparent
          opacity={0.15}
          side={THREE.DoubleSide}
          depthWrite={false}
        />
      </mesh>
      {/* Wireframe overlay */}
      <mesh>
        <sphereGeometry args={[1, 16, 16]} />
        <meshBasicMaterial color="#27272a" wireframe transparent opacity={0.4} />
      </mesh>
    </>
  );
}

function AxisLine({
  start,
  end,
  color,
}: {
  start: [number, number, number];
  end: [number, number, number];
  color: string;
}) {
  return <Line points={[start, end]} color={color} lineWidth={1} transparent opacity={0.5} />;
}

function AxisLabels() {
  const labelProps = {
    fontSize: 0.12,
    anchorX: "center" as const,
    anchorY: "middle" as const,
  };

  return (
    <>
      {/* Z axis labels */}
      <Text position={[0, 0, 1.2]} color={Z_COLOR} {...labelProps}>
        {"|0\u27E9"}
      </Text>
      <Text position={[0, 0, -1.2]} color={Z_COLOR} {...labelProps}>
        {"|1\u27E9"}
      </Text>
      {/* X axis labels */}
      <Text position={[1.2, 0, 0]} color={X_COLOR} {...labelProps}>
        {"|+\u27E9"}
      </Text>
      <Text position={[-1.2, 0, 0]} color={X_COLOR} {...labelProps}>
        {"|-\u27E9"}
      </Text>
      {/* Y axis labels */}
      <Text position={[0, 1.2, 0]} color="#a1a1aa" {...labelProps}>
        Y
      </Text>
      <Text position={[0, -1.2, 0]} color="#a1a1aa" {...labelProps}>
        -Y
      </Text>
      {/* Axis name labels */}
      <Text position={[0, 0, 1.4]} color="#a1a1aa" fontSize={0.08}>
        Z
      </Text>
      <Text position={[1.4, 0, 0]} color="#a1a1aa" fontSize={0.08}>
        X
      </Text>
    </>
  );
}

function StateArrow({
  target,
  color,
}: {
  target: readonly [number, number, number];
  color: string;
}) {
  const meshRef = useRef<THREE.Mesh>(null);
  const tipRef = useRef<THREE.Mesh>(null);
  const currentPos = useRef(new THREE.Vector3(target[0], target[1], target[2]));

  useFrame(() => {
    const mesh = meshRef.current;
    const tip = tipRef.current;
    if (!mesh) return;

    const dest = new THREE.Vector3(target[0], target[1], target[2]);
    currentPos.current.lerp(dest, 0.08);

    const pos = currentPos.current;
    const len = pos.length();
    if (len < 0.001) return;

    // Position the cylinder so it goes from origin to the current point
    const dir = pos.clone().normalize();
    mesh.position.copy(dir.clone().multiplyScalar(len / 2));
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
    mesh.scale.set(1, len, 1);

    if (tip) {
      tip.position.copy(pos);
    }
  });

  return (
    <>
      {/* Arrow shaft */}
      <mesh ref={meshRef}>
        <cylinderGeometry args={[0.02, 0.02, 1, 8]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.3} />
      </mesh>
      {/* Tip sphere at the state point */}
      <mesh ref={tipRef}>
        <sphereGeometry args={[0.05, 16, 16]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.5} />
      </mesh>
    </>
  );
}

function EquatorCircle() {
  const points = useMemo(() => {
    const pts: [number, number, number][] = [];
    for (let i = 0; i <= 64; i++) {
      const angle = (i / 64) * Math.PI * 2;
      pts.push([Math.cos(angle), 0, Math.sin(angle)]);
    }
    return pts;
  }, []);

  return <Line points={points} color="#27272a" lineWidth={1} transparent opacity={0.6} />;
}

function MeridianCircle() {
  const points = useMemo(() => {
    const pts: [number, number, number][] = [];
    for (let i = 0; i <= 64; i++) {
      const angle = (i / 64) * Math.PI * 2;
      pts.push([Math.cos(angle), Math.sin(angle), 0]);
    }
    return pts;
  }, []);

  return <Line points={points} color="#27272a" lineWidth={1} transparent opacity={0.6} />;
}

function BlochScene({ stateVector, basis }: BlochSphereProps) {
  const arrowColor = basis === "Z" ? Z_COLOR : X_COLOR;

  return (
    <>
      <ambientLight intensity={0.4} />
      <directionalLight position={[5, 5, 5]} intensity={0.6} />
      <directionalLight position={[-3, -3, 2]} intensity={0.3} />

      <SphereWireframe />
      <EquatorCircle />
      <MeridianCircle />

      {/* Axes */}
      <AxisLine start={[0, 0, -1.3]} end={[0, 0, 1.3]} color="#27272a" />
      <AxisLine start={[-1.3, 0, 0]} end={[1.3, 0, 0]} color="#27272a" />
      <AxisLine start={[0, -1.3, 0]} end={[0, 1.3, 0]} color="#27272a" />

      <AxisLabels />
      <StateArrow target={stateVector} color={arrowColor} />

      <OrbitControls enablePan={false} minDistance={2} maxDistance={5} />
    </>
  );
}

export function BlochSphere({ stateVector, basis }: BlochSphereProps) {
  return (
    <div className="bloch-sphere-container">
      <Canvas
        camera={{ position: [1.8, 1.4, 1.8], fov: 45 }}
        gl={{ antialias: true, alpha: true }}
        style={{ background: "transparent" }}
      >
        <BlochScene stateVector={stateVector} basis={basis} />
      </Canvas>
    </div>
  );
}
