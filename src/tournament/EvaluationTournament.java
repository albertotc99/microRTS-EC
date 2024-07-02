package tournament;

import java.io.File;
import java.io.FileWriter;
import java.io.Writer;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import GNS.EconomyLightRush;
import ai.RandomBiasedAI;
import ai.abstraction.LightRush;
import ai.abstraction.WorkerRush;
import ai.core.AI;
import ai.mcts.naivemcts.NaiveMCTS;
import myAgent.MyAgent;
import rts.units.UnitTypeTable;
import tournaments.FixedOpponentsTournament;

public class EvaluationTournament {

  public static void main(String[] args) {
    // Parsear los parámetros
    double[] doubleParams = new double[8];
    int[] intParams = new int[2];
    UnitTypeTable utt = new UnitTypeTable();    
    AI agent = new MyAgent(utt);

    if (args.length != 10) {
      System.err.println("Debe proporcionar exactamente 10 parámetros.");
      System.exit(1);
      // agent = new MyAgent(utt, 0.2, 0.82, 0.85, 3, 0, 0.7, 0.4, 0.3, 0.12, 0.25);
      // agent = new MyAgent(utt, 0.2, 0.95, 0.9, 3, 0, 0.3, 0.4, 0.3, 0.08, 0.1);
      // agent = new MyAgent(utt, 0.2, 1, 0.8, 3, 20, 0, 0, 0, 0.08, 0.1);

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

        // Verifify and assign 5 last doubles
        for (int i = 0; i < 5; i++) {
            doubleParams[i + 3] = Double.parseDouble(args[i + 5]);
            if (doubleParams[i + 3] < 0.0 || doubleParams[i + 3] > 1.0) {
                throw new IllegalArgumentException("Todos los parámetros double deben estar entre 0 y 1.");
            }
        }

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
                doubleParams[6], doubleParams[7]);
    }

    List<AI> selectedAIs = new ArrayList<>();
    selectedAIs.add(agent);
    // selectedAIs.add(new MyAgent(utt));

    List<AI> opponentAIs = new ArrayList<>();
    // opponentAIs.add(new WorkerRush(utt));
    // opponentAIs.add(new EconomyLightRush(utt));
    opponentAIs.add(new LightRush(utt));
    opponentAIs.add(new EconomyLightRush(utt));
    // opponentAIs.add(new RandomBiasedAI(utt));
    opponentAIs.add(new NaiveMCTS(utt));
    // ai2 = new RandomBiasedAI();
    // ai2 = new WorkerRushPlusPlus(utt);
    // ai2 = new WorkerRush(utt);
    // ai2 = new RangedRush(utt);
    // ai2 = new HeavyRush(utt);
    // ai2 = new EconomyMilitaryRush(utt);
    // ai2 = new HeavyDefense(utt);
    // ai2 = new LightDefense(utt);
    // ai2 = new RangedDefense(utt);
    // ai2 = new RangedRushPlan(utt);
    // ai2 = new TwoPhaseNaiveMCTS(utt);
    // ai2 = new MonteCarlo(utt);
    // ai2 = new BS3_NaiveMCTS(utt);
    // ai2 = new SCV(utt);
    // ai2 = new InformedNaiveMCTS(utt); // no se puede probar, falla
    // ai2 = new IDRTMinimax(utt);
    // ai2 = new AHTNAI(utt); // también falla
    // ai2 = new MLPSMCTS(utt);
    // ai2 = new UCTFirstPlayUrgency(utt);

    String [] mapsString = {
        // "maps/melee14x12Mixed18.xml",
        "maps/16x16/basesWorkers16x16A.xml",
        "maps/basesWorkers32x32A.xml",
        "maps/barricades24x24.xml",
        // "maps/8x8/FourBasesWorkers8x8.xml",
        // "maps/16x16/TwoBasesBarracks16x16.xml",
        "maps/NoWhereToRun9x8.xml",
        "maps/chambers32x32.xml",
        // "maps/GardenOfWar64x64.xml",
        "maps/BroodWar/(2)Benzene.scxA.xml",
        // "maps/BroodWar/(2)Destination.scxA.xml",
        // "maps/BroodWar/(4)Andromeda.scxB.xml"
    };
    List<String> maps = Arrays.asList(mapsString);
    int iterations = 4;
    int maxGameLength = 10000;
    int timeBudget = 100;
    int iterationsBudget = -1;
    int preAnalysisBudget = 0;
    boolean fullObservability = true;
    boolean timeOutCheck = true;
    boolean gcCheck = true;
    boolean preGameAnalysis = preAnalysisBudget > 0;
    // String prefix = "./fitness/tournament_";
    String prefix = "./FirstExecGA/tournament_";
    int idx = 0;
    File file;
    do {
        idx++;
        file = new File(prefix + idx);
    }while(file.exists());
    file.mkdir();
    String tournamentfolder = file.getPath();
    final File fileToUse = new File(tournamentfolder + "/tournament.csv");
    final String tracesFolder = (tournamentfolder + "/traces");

    try {
      System.out.print(tournamentfolder + "/tournament.csv");
      Writer writer = new FileWriter(fileToUse);
      new FixedOpponentsTournament(selectedAIs, opponentAIs).runTournament(maps,
                                          iterations, maxGameLength, timeBudget, iterationsBudget, 
                                          preAnalysisBudget, 100, // 1000 is just to give 1 second to the AIs to load their read/write folder saved content
                                          fullObservability, timeOutCheck, gcCheck, preGameAnalysis, 
                                          utt, tracesFolder,
                                          writer, null,
                                          tournamentfolder);

      writer.close();
    } catch (Exception e) {
      // TODO Auto-generated catch block
      e.printStackTrace();
    }
    
  }
}
