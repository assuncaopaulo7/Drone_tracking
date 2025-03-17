![MavSDK Drone and Plane Simulation](https://via.placeholder.com/800x400.png?text=Drone+and+Plane+Simulation+in+Gazebo)

<!DOCTYPE html>
<html>

<body>
  <h1>Simulação de Drone e Avião no Gazebo com MAVSDK</h1>
  <p>Este repositório contém um script para lançamento de uma simulação no Gazebo com um drone e um avião, utilizando o MAVSDK para controle. O projeto inclui alterações no código original de drones para suportar a interação entre drone e avião.</p>

  <h2>Instruções de Uso:</h2>
  <p>Para lançar a simulação no Gazebo e executar o código, siga os passos abaixo:</p>
  <ol>
    <li>Lançar o Gazebo:</li>
    <pre><code>cd
cd multivehicle
cd MavSDK-Final-Project
./script.sh</code></pre>
    <li>Rodar o código:</li>
    <pre><code>python3 offboard_multiple_from_csv_test.py</code></pre>
  </ol>

  <h2>O que foi feito:</h2>
  <ul>
    <li>Script para lançamento do Gazebo com um drone e um avião.</li>
    <li>Alterações no código de drones para suportar a simulação de drone e avião.</li>
  </ul>

  <h2>O que falta fazer:</h2>
  <ul>
    <li>Mudar a trajetória do avião para um padrão mais complexo ou personalizado.</li>
    <li>Verificar e resolver problemas de conexão entre o MAVSDK e a simulação.</li>
  </ul>

  <h2>Introdução:</h2>
  <p>O MAVSDK (MAVLink SDK) é uma ferramenta poderosa para interagir com drones e veículos aéreos usando o protocolo de comunicação MAVLink. Este projeto utiliza o modo "offboard" do PX4 para controlar a posição e a velocidade do drone e do avião em uma simulação no Gazebo.</p>
  <a href="https://mavsdk.mavlink.io/main/en/">Documentação do MAVSDK</a>

  <h2>Pré-requisitos:</h2>
  <p>Para executar o código e seguir o projeto, certifique-se de ter os seguintes pré-requisitos:</p>
  <ul>
    <li>Python: Instale o Python e as dependências necessárias para executar os scripts.</li>
    <li>Ambiente de Desenvolvimento PX4 para SITL: Configure um ambiente de simulação PX4 Software-in-the-Loop (SITL) no Ubuntu ou WSL-2.</li>
    <li>MAVSDK: Instale o MAVSDK para comunicação com o drone e o avião.</li>
  </ul>

  <h2>Próximos passos:</h2>
  <ul>
    <li>Implementar uma nova trajetória para o avião.</li>
    <li>Resolver problemas de conexão e otimizar a comunicação com o MAVSDK.</li>
  </ul>


</body>
</html>