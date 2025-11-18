package tournament;

import java.io.File;
import java.io.FileWriter;
import java.io.Writer;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import ai.core.AI;
import myAgent.MyAgent;
import rts.units.UnitTypeTable;
import tournaments.RoundRobinTournament;

public class CoEvEvaluationGame {

  public static void main(String[] args) {
    List<AI> agents = new ArrayList<>();
    UnitTypeTable utt = new UnitTypeTable();
    
  // Verificar que se reciban 22 o 23 parámetros (11 por agente + opcional nombre de archivo)
  if (args.length != 22 && args.length != 23) {
    System.err.println("Debe proporcionar 22 parámetros (11 para cada agente) o 23 (incluyendo nombre de archivo).");
    System.exit(1);
  }
    
    //System.out.println("DEBUG: ===== COEV EVALUATION GAME =====");
    //System.out.println("DEBUG: Recibidos " + args.length + " parámetros");
    
  // Crear primer agente con los primeros 11 parámetros
  String[] params1 = Arrays.copyOfRange(args, 0, 11);
    //System.out.println("DEBUG: Creando Agente 1 con parámetros: " + Arrays.toString(params1));
    MyAgent agent1 = createMyAgentFromParams(params1, utt);
    agents.add(agent1);
    
  // Crear segundo agente con los siguientes 11 parámetros
  String[] params2 = Arrays.copyOfRange(args, 11, 22);
    //System.out.println("DEBUG: Creando Agente 2 con parámetros: " + Arrays.toString(params2));
    MyAgent agent2 = createMyAgentFromParams(params2, utt);
    agents.add(agent2);

    //System.out.println("DEBUG: Agentes creados para el enfrentamiento:");
    //System.out.println("DEBUG: Agente 1: " + agent1.toString());
    //System.out.println("DEBUG: Agente 2: " + agent2.toString());
    //System.out.println("DEBUG: =====================================");

    String [] mapsString = {
        //"maps/melee14x12Mixed18.xml",
        "maps/16x16/basesWorkers16x16A.xml",
        ///"maps/basesWorkers32x32A.xml",
        "maps/BWDistantResources32x32.xml",
        ///"maps/barricades24x24.xml",
        //"maps/8x8/FourBasesWorkers8x8.xml",
        ///"maps/16x16/TwoBasesBarracks16x16.xml",
        // "maps/NoWhereToRun9x8.xml",
        ///"maps/chambers32x32.xml",
        ///"maps/GardenOfWar64x64.xml",
        "maps/DoubleGame24x24.xml",
        "maps/BroodWar/(2)Benzene.scxA.xml",
        "maps/BroodWar/(2)Destination.scxA.xml",
        // "maps/BroodWar/(4)Andromeda.scxB.xml"
    };
    List<String> maps = Arrays.asList(mapsString);
    int iterations = 2;
    int maxGameLength = 14000;
    int timeBudget = 100;
    int iterationsBudget = -1;
    int preAnalysisBudget = 0;
    boolean fullObservability = true;
    boolean timeOutCheck = true;
    boolean gcCheck = true;
    boolean selfMatches = false;
    boolean preGameAnalysis = preAnalysisBudget > 0;
    // String folder = "./resultados/CoEvELO";

    // // Crear la carpeta si no existe
    // File directory = new File(folder);
    // if (!directory.exists()) {
    //   directory.mkdirs();
    // }

    // Obtener nombre de archivo del parámetro 21 o usar valor por defecto
    String tournamentName = "tournament_1.csv";
  if (args.length == 23) {
    tournamentName = args[22]; // El último parámetro es el nombre del archivo
    }
    
    //String prefix = folder + "/" + tournamentName;
    //String fileName = prefix + ".csv";
    String fileName = tournamentName;
    File file = new File(fileName);

    try {
      System.out.print(file.getPath());
      Writer writer = new FileWriter(file);
      new RoundRobinTournament(agents).runTournament(-1, maps,
                                          iterations, maxGameLength, timeBudget, iterationsBudget, 
                                          preAnalysisBudget, 1000, // 1000 is just to give 1 second to the AIs to load their read/write folder saved content
                                          fullObservability, selfMatches, timeOutCheck, gcCheck, preGameAnalysis, 
                                          utt, null,
                                          writer, null,
                                          null);

      writer.flush(); // Asegurar que se escriba todo a la terminal
    } catch (Exception e) {
      // TODO Auto-generated catch block
      e.printStackTrace();
    }
    
  }

  // Parsear los parámetros y crear el agente
  private static MyAgent createMyAgentFromParams(String[] args, UnitTypeTable utt){
    double[] doubleParams = new double[8]; // dEnemyDanger, pUnits, pTime, probLight, probRange, probHeavy, dBaseBarracks, dUnitBuilding
    int[] intParams = new int[2]; // nHarvestWorkers, nAttackWorkers
    String extraParam = ""; // parámetro string extra
    MyAgent agent = new MyAgent(utt);

    if (args.length != 11) {
      System.err.println("Debe proporcionar exactamente 11 parámetros (10 numéricos + 1 string).");
      System.exit(1);
      agent = new MyAgent(utt, 0.2, 0.82, 0.85, 3, 0, 0.7, 0.4, 0.3, 0.12, 0.25, "");
    } else {
      try {
        // Verify and assign the first 3 doubles
        for (int i = 0; i < 3; i++) {
            doubleParams[i] = Double.parseDouble(args[i]);
            if (doubleParams[i] < 0.0 || doubleParams[i] > 1.0) {
                throw new IllegalArgumentException("Todos los parámetros double deben estar entre 0 y 1.");
            }
        }

        // Verify and assign 2 integers
        for (int i = 0; i < 2; i++) {
            intParams[i] = Integer.parseInt(args[i + 3]);
            if (intParams[i] > 30 || intParams[i] < 0) {
                throw new IllegalArgumentException("Todos los parámetros int deben estar entre 0 y 30.");
            }
        }

        // Verify and assign 5 last doubles
        for (int i = 0; i < 5; i++) {
            doubleParams[i + 3] = Double.parseDouble(args[i + 5]);
            if (doubleParams[i + 3] < 0.0 || doubleParams[i + 3] > 1.0) {
                throw new IllegalArgumentException("Todos los parámetros double deben estar entre 0 y 1.");
            }
        }

        // Extra string parameter (index 10)
        extraParam = args[10];

      } catch (NumberFormatException e) {
          System.err.println("Todos los parámetros deben ser números.");
          System.exit(1);
      } catch (IllegalArgumentException e) {
          System.err.println(e.getMessage());
          System.exit(1);
      }
      
      agent = new MyAgent(utt, doubleParams[0], doubleParams[1], doubleParams[2], 
                intParams[0], intParams[1], 
                doubleParams[3], doubleParams[4], doubleParams[5], 
                doubleParams[6], doubleParams[7], extraParam);
      
      // System.out.println("DEBUG: Agente creado con parámetros parseados: [" + 
      //                    doubleParams[0] + ", " + doubleParams[1] + ", " + doubleParams[2] + ", " +
      //                    intParams[0] + ", " + intParams[1] + ", " +
      //                    doubleParams[3] + ", " + doubleParams[4] + ", " + doubleParams[5] + ", " +
      //                    doubleParams[6] + ", " + doubleParams[7] + "]");
    }

    return agent;
  }

}
