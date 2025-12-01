import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Sphere, MeshDistortMaterial, Html } from '@react-three/drei';

export function Orb({ mood }) {
  const materialRef = useRef();

  // "Calm" (True) = Smooth, Blue/Teal
  // "Spikey" (False/Fake) = Distorted, Red/Magenta
  const isChaos = mood === 'spikey';
  
  useFrame((state) => {
    // Slowly animate the distortion speed
    if (materialRef.current) {
        materialRef.current.time = state.clock.getElapsedTime();
    }
  });

  return (
    <Sphere args={[1, 64, 64]} scale={2.5}>
      <MeshDistortMaterial
        ref={materialRef}
        color={isChaos ? "#ff0055" : "#00f0ff"} // Hero Colors
        attach="material"
        distort={isChaos ? 0.6 : 0.1} // The "Spikey" Factor
        speed={isChaos ? 4 : 1.5}     // Speed of movement
        roughness={0.2}
        metalness={0.9}
      />
    </Sphere>
  );
}