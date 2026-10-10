import sharp from 'sharp';
await sharp('outputs/system-diagram/network_infrastructure_diagram_updated.svg').resize(3200).png().toFile('outputs/system-diagram/network_infrastructure_diagram_updated.png');
